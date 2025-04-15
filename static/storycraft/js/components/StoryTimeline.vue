<template>
  <div class="story-timeline-container">
    <div class="timeline-controls">
      <div class="filter-buttons">
        <button 
          v-for="plotType in plotTypes" 
          :key="plotType.id"
          :class="['filter-btn', { active: activePlots.includes(plotType.id) }]"
          :style="{ borderColor: plotType.color }"
          @click="togglePlotFilter(plotType.id)"
        >
          {{ plotType.name }}
        </button>
      </div>
      <div class="zoom-controls">
        <button @click="zoom(0.2)" class="zoom-btn">
          <i class="fas fa-search-plus"></i>
        </button>
        <button @click="zoom(-0.2)" class="zoom-btn">
          <i class="fas fa-search-minus"></i>
        </button>
        <button @click="resetView()" class="zoom-btn">
          <i class="fas fa-expand"></i>
        </button>
      </div>
    </div>
    
    <div class="timeline-container" ref="timelineContainer">
      <!-- Timeline will be rendered here -->
      <div v-if="loading" class="timeline-loading">
        <div class="spinner"></div>
        <p>Building timeline...</p>
      </div>
      
      <div class="timeline-wrapper" ref="timelineWrapper" v-show="!loading">
        <!-- Track headers -->
        <div class="timeline-headers">
          <div class="timeline-scale-header"></div>
          <div 
            v-for="track in visibleTracks" 
            :key="track.id"
            class="timeline-track-header"
          >
            <div class="track-header-content">
              <i :class="getTrackIcon(track)"></i>
              <span>{{ track.name }}</span>
            </div>
          </div>
        </div>
        
        <!-- Timeline content -->
        <div class="timeline-content" @wheel="handleWheel" ref="timelineContent">
          <!-- Time scale -->
          <div class="timeline-scale">
            <div 
              v-for="tick in timeScaleTicks" 
              :key="tick.position"
              class="timeline-tick"
              :style="{ left: tick.position + 'px' }"
            >
              <div class="tick-line"></div>
              <div class="tick-label">{{ tick.label }}</div>
            </div>
          </div>
          
          <!-- Timeline tracks -->
          <div 
            v-for="track in visibleTracks" 
            :key="track.id"
            class="timeline-track"
          >
            <!-- Scenes in this track -->
            <div 
              v-for="item in getTrackItems(track)" 
              :key="item.id"
              class="timeline-item"
              :class="{ 'item-selected': selectedItem && selectedItem.id === item.id }"
              :style="getItemStyle(item)"
              @click="selectItem(item)"
            >
              <div class="item-content">
                <div class="item-title">{{ item.name }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Item details panel -->
    <div class="item-details" v-if="selectedItem">
      <div class="item-details-header">
        <div class="item-type">
          <i :class="getItemTypeIcon(selectedItem)"></i>
          <span>{{ selectedItem.type }}</span>
        </div>
        <h3>{{ selectedItem.name }}</h3>
        <button class="close-btn" @click="selectedItem = null">×</button>
      </div>
      
      <div class="item-details-content">
        <p v-if="selectedItem.description">{{ selectedItem.description }}</p>
        
        <div v-if="selectedItem.type === 'Scene'">
          <div class="item-details-section">
            <h4>Setting</h4>
            <p v-if="getSceneSetting(selectedItem)">{{ getSceneSetting(selectedItem).name }}</p>
            <p v-else>No setting assigned</p>
          </div>
          
          <div class="item-details-section">
            <h4>Characters</h4>
            <ul v-if="getSceneCharacters(selectedItem).length">
              <li v-for="char in getSceneCharacters(selectedItem)" :key="char.id">
                {{ char.name }}
              </li>
            </ul>
            <p v-else>No characters in this scene</p>
          </div>
          
          <div class="item-details-section" v-if="selectedItem.metadata">
            <h4>Details</h4>
            <dl class="item-metadata">
              <template v-for="(value, key) in selectedItem.metadata">
                <dt :key="'dt-' + key">{{ formatMetadataKey(key) }}</dt>
                <dd :key="'dd-' + key">{{ value }}</dd>
              </template>
            </dl>
          </div>
        </div>
        
        <div class="item-actions">
          <button @click="editItem(selectedItem)" class="action-btn">
            <i class="fas fa-edit"></i> Edit
          </button>
          <button @click="viewItem(selectedItem)" class="action-btn">
            <i class="fas fa-eye"></i> View Details
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StoryTimeline',
  props: {
    storyId: {
      type: Number,
      required: true
    },
    apiUrl: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      loading: true,
      storyData: null,
      selectedItem: null,
      
      // Timeline configuration
      timelineConfig: {
        scale: 100, // pixels per unit
        minScale: 50,
        maxScale: 300,
        viewportWidth: 1000,
        viewportScrollLeft: 0
      },
      
      // Filters
      activePlots: [],
      
      // Track configuration
      trackTypes: [
        { id: 'characters', label: 'Characters', visible: true },
        { id: 'settings', label: 'Settings', visible: true },
        { id: 'scenes', label: 'Scenes', visible: true }
      ]
    };
  },
  computed: {
    // Plot types with colors for filtering
    plotTypes() {
      if (!this.storyData) return [];
      
      return this.storyData.plots.map((plot, index) => {
        const colors = ['#4285F4', '#EA4335', '#FBBC05', '#34A853', '#9C27B0', '#FF5722'];
        return {
          id: plot.id,
          name: plot.name,
          color: colors[index % colors.length]
        };
      });
    },
    
    // All available tracks
    allTracks() {
      if (!this.storyData) return [];
      
      // Create character tracks
      const characterTracks = this.storyData.characters.map(char => ({
        id: `character-${char.id}`,
        type: 'character',
        name: char.name,
        entityId: char.id
      }));
      
      // Create setting tracks
      const settingTracks = this.storyData.settings.map(setting => ({
        id: `setting-${setting.id}`,
        type: 'setting',
        name: setting.name,
        entityId: setting.id
      }));
      
      // Create plot tracks
      const plotTracks = this.storyData.plots.map(plot => ({
        id: `plot-${plot.id}`,
        type: 'plot',
        name: plot.name,
        entityId: plot.id
      }));
      
      return [...characterTracks, ...settingTracks, ...plotTracks];
    },
    
    // Visible tracks based on filters
    visibleTracks() {
      if (!this.allTracks) return [];
      
      // If no plot filters are active, show all
      if (this.activePlots.length === 0) {
        return this.allTracks;
      }
      
      // Filter tracks by active plots
      return this.allTracks.filter(track => {
        if (track.type === 'plot') {
          return this.activePlots.includes(track.entityId);
        }
        
        // For character and setting tracks, check if they have scenes in active plots
        const entityId = track.entityId;
        const hasSceneInActivePlot = this.storyData.scenes.some(scene => {
          if (!this.activePlots.includes(scene.plot_id)) return false;
          
          if (track.type === 'character') {
            return scene.characters.includes(entityId);
          } else if (track.type === 'setting') {
            return scene.setting_id === entityId;
          }
          return false;
        });
        
        return hasSceneInActivePlot;
      });
    },
    
    // Time scale ticks for the timeline
    timeScaleTicks() {
      if (!this.storyData || !this.storyData.scenes.length) return [];
      
      // Use scene sequence numbers as time units
      const minSequence = 0;
      const maxSequence = Math.max(...this.storyData.scenes.map(s => s.sequence_number || 0)) + 1;
      
      // Create a tick every N units, depending on scale
      const tickInterval = this.timelineConfig.scale < 100 ? 5 : 
                          (this.timelineConfig.scale < 200 ? 2 : 1);
      
      const ticks = [];
      for (let i = minSequence; i <= maxSequence; i += tickInterval) {
        ticks.push({
          position: i * this.timelineConfig.scale,
          label: `Scene ${i}`
        });
      }
      
      return ticks;
    }
  },
  mounted() {
    this.fetchStoryData();
    window.addEventListener('resize', this.updateTimelineDimensions);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.updateTimelineDimensions);
  },
  methods: {
    async fetchStoryData() {
      this.loading = true;
      try {
        // In a real implementation, this would fetch from this.apiUrl
        // For now, simulate a network request with mock data
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Mock data structure - similar to the one in StoryGraph.vue
        this.storyData = {
          id: this.storyId,
          title: "The Hero's Journey",
          characters: [
            { id: 1, type: 'Character', name: 'Elara', description: 'The protagonist' },
            { id: 2, type: 'Character', name: 'Kaden', description: 'The mentor' },
            { id: 3, type: 'Character', name: 'Vex', description: 'The antagonist' }
          ],
          settings: [
            { id: 1, type: 'Setting', name: 'Forest of Whispers', description: 'A mysterious wooded area' },
            { id: 2, type: 'Setting', name: 'Mountain Peak', description: 'A treacherous summit' },
            { id: 3, type: 'Setting', name: 'Ancient Temple', description: 'A forgotten place of power' }
          ],
          plots: [
            { id: 1, type: 'Plot', name: 'Main Quest', description: 'The primary story arc' },
            { id: 2, type: 'Plot', name: 'Kaden\'s Past', description: 'The mentor\'s backstory' }
          ],
          scenes: [
            { 
              id: 1, 
              type: 'Scene', 
              name: 'The Call', 
              description: 'Elara receives a mysterious message',
              setting_id: 1,
              plot_id: 1,
              sequence_number: 1,
              characters: [1],
              metadata: {
                time_of_day: 'Dawn',
                weather: 'Foggy',
                mood: 'Mysterious'
              }
            },
            { 
              id: 2, 
              type: 'Scene', 
              name: 'The Meeting', 
              description: 'Elara meets her mentor Kaden',
              setting_id: 1,
              plot_id: 1,
              sequence_number: 2,
              characters: [1, 2],
              metadata: {
                time_of_day: 'Morning',
                weather: 'Clear',
                mood: 'Hopeful'
              }
            },
            { 
              id: 3, 
              type: 'Scene', 
              name: 'Kaden\'s Revelation', 
              description: 'Kaden reveals his connection to the temple',
              setting_id: 1,
              plot_id: 2,
              sequence_number: 3,
              characters: [2],
              metadata: {
                time_of_day: 'Evening',
                weather: 'Rainy',
                mood: 'Somber'
              }
            },
            { 
              id: 4, 
              type: 'Scene', 
              name: 'The Confrontation', 
              description: 'Elara confronts Vex at the temple',
              setting_id: 3,
              plot_id: 1,
              sequence_number: 4,
              characters: [1, 3],
              metadata: {
                time_of_day: 'Night',
                weather: 'Stormy',
                mood: 'Tense'
              }
            },
            { 
              id: 5, 
              type: 'Scene', 
              name: 'The Summit', 
              description: 'Final battle at the mountain peak',
              setting_id: 2,
              plot_id: 1,
              sequence_number: 5,
              characters: [1, 2, 3],
              metadata: {
                time_of_day: 'Noon',
                weather: 'Sunny',
                mood: 'Climactic'
              }
            }
          ]
        };
        
        // Initialize active plots
        this.activePlots = this.storyData.plots.map(plot => plot.id);
        
        // Update timeline dimensions
        this.$nextTick(() => {
          this.updateTimelineDimensions();
          this.loading = false;
        });
      } catch (error) {
        console.error('Error fetching story data:', error);
        this.loading = false;
      }
    },
    updateTimelineDimensions() {
      if (!this.$refs.timelineContainer) return;
      
      // Update viewport dimensions
      const containerWidth = this.$refs.timelineContainer.clientWidth;
      this.timelineConfig.viewportWidth = containerWidth;
      
      // If we have a content element, make sure it's wide enough
      if (this.$refs.timelineContent) {
        const contentWidth = this.calculateContentWidth();
        this.$refs.timelineContent.style.width = `${contentWidth}px`;
      }
    },
    calculateContentWidth() {
      if (!this.storyData || !this.storyData.scenes.length) return 1000;
      
      // Calculate based on the highest sequence number plus some padding
      const maxSequence = Math.max(...this.storyData.scenes.map(s => s.sequence_number || 0));
      const contentWidth = (maxSequence + 2) * this.timelineConfig.scale;
      
      // Ensure it's at least as wide as the viewport
      return Math.max(contentWidth, this.timelineConfig.viewportWidth);
    },
    getTrackItems(track) {
      if (!this.storyData) return [];
      
      const items = [];
      
      if (track.type === 'character') {
        // For a character track, add all scenes where this character appears
        const characterId = track.entityId;
        this.storyData.scenes.forEach(scene => {
          if (scene.characters.includes(characterId)) {
            items.push({
              id: `scene-${scene.id}-char-${characterId}`,
              name: scene.name,
              type: 'Scene',
              sceneId: scene.id,
              position: scene.sequence_number,
              plotId: scene.plot_id,
              description: scene.description,
              metadata: scene.metadata
            });
          }
        });
      } else if (track.type === 'setting') {
        // For a setting track, add all scenes in this setting
        const settingId = track.entityId;
        this.storyData.scenes.forEach(scene => {
          if (scene.setting_id === settingId) {
            items.push({
              id: `scene-${scene.id}-setting-${settingId}`,
              name: scene.name,
              type: 'Scene',
              sceneId: scene.id,
              position: scene.sequence_number,
              plotId: scene.plot_id,
              description: scene.description,
              metadata: scene.metadata
            });
          }
        });
      } else if (track.type === 'plot') {
        // For a plot track, add all scenes in this plot
        const plotId = track.entityId;
        this.storyData.scenes.forEach(scene => {
          if (scene.plot_id === plotId) {
            items.push({
              id: `scene-${scene.id}-plot-${plotId}`,
              name: scene.name,
              type: 'Scene',
              sceneId: scene.id,
              position: scene.sequence_number,
              plotId: scene.plot_id,
              description: scene.description,
              metadata: scene.metadata
            });
          }
        });
      }
      
      return items;
    },
    getItemStyle(item) {
      // Position based on sequence number
      const left = (item.position * this.timelineConfig.scale) + 'px';
      
      // Set width proportional to scene complexity
      const width = (this.timelineConfig.scale * 0.8) + 'px';
      
      // Set background color based on plot
      const plotColor = this.getPlotColor(item.plotId);
      
      return {
        left,
        width,
        backgroundColor: plotColor
      };
    },
    getPlotColor(plotId) {
      const plotIndex = this.plotTypes.findIndex(p => p.id === plotId);
      if (plotIndex >= 0) {
        return this.plotTypes[plotIndex].color;
      }
      return '#9AA0A6'; // Default color
    },
    getTrackIcon(track) {
      switch (track.type) {
        case 'character': return 'fas fa-user';
        case 'setting': return 'fas fa-map-marker-alt';
        case 'plot': return 'fas fa-project-diagram';
        default: return 'fas fa-circle';
      }
    },
    getItemTypeIcon(item) {
      return 'fas fa-file-alt'; // Scene icon
    },
    getSceneSetting(scene) {
      if (!this.storyData || !scene) return null;
      
      const settingId = this.storyData.scenes.find(s => s.id === scene.sceneId)?.setting_id;
      return this.storyData.settings.find(setting => setting.id === settingId);
    },
    getSceneCharacters(scene) {
      if (!this.storyData || !scene) return [];
      
      const sceneData = this.storyData.scenes.find(s => s.id === scene.sceneId);
      if (!sceneData) return [];
      
      return this.storyData.characters.filter(char => 
        sceneData.characters.includes(char.id)
      );
    },
    formatMetadataKey(key) {
      // Convert camelCase or snake_case to Title Case
      return key
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, str => str.toUpperCase());
    },
    selectItem(item) {
      this.selectedItem = item;
    },
    editItem(item) {
      // This would link to the scene editor
      const sceneId = item.sceneId;
      this.$emit('edit-scene', sceneId);
    },
    viewItem(item) {
      // This would link to the scene detail view
      const sceneId = item.sceneId;
      this.$emit('view-scene', sceneId);
    },
    togglePlotFilter(plotId) {
      const index = this.activePlots.indexOf(plotId);
      if (index >= 0) {
        // Remove plot from active filters
        this.activePlots.splice(index, 1);
      } else {
        // Add plot to active filters
        this.activePlots.push(plotId);
      }
    },
    zoom(delta) {
      // Calculate new scale
      const newScale = Math.max(
        this.timelineConfig.minScale,
        Math.min(
          this.timelineConfig.maxScale,
          this.timelineConfig.scale + (this.timelineConfig.scale * delta)
        )
      );
      
      // Apply new scale
      this.timelineConfig.scale = newScale;
      
      // Update timeline width
      this.updateTimelineDimensions();
    },
    resetView() {
      // Reset to default scale
      this.timelineConfig.scale = 100;
      
      // Reset scroll position
      if (this.$refs.timelineContent) {
        this.$refs.timelineContent.scrollLeft = 0;
      }
      
      // Update dimensions
      this.updateTimelineDimensions();
    },
    handleWheel(event) {
      // Prevent default browser behavior (page scrolling)
      event.preventDefault();
      
      if (event.ctrlKey || event.metaKey) {
        // Zoom with Ctrl+wheel
        const delta = event.deltaY > 0 ? -0.1 : 0.1;
        this.zoom(delta);
      } else {
        // Regular scrolling
        if (this.$refs.timelineContent) {
          this.$refs.timelineContent.scrollLeft += event.deltaX;
        }
      }
    }
  }
};
</script>

<style scoped>
.story-timeline-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}

.timeline-controls {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
}

.filter-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 5px 10px;
  border: 2px solid;
  border-radius: 4px;
  background-color: white;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.filter-btn.active {
  background-color: rgba(0, 0, 0, 0.05);
  font-weight: 500;
}

.zoom-controls {
  display: flex;
  gap: 5px;
}

.zoom-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 4px;
  background-color: #e0e0e0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.zoom-btn:hover {
  background-color: #d0d0d0;
}

.timeline-container {
  flex-grow: 1;
  position: relative;
  overflow: hidden;
  min-height: 400px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  margin-top: 16px;
}

.timeline-loading {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.8);
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 2s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.timeline-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.timeline-headers {
  display: flex;
  border-bottom: 1px solid #e0e0e0;
  background-color: #f9f9f9;
}

.timeline-scale-header {
  width: 150px;
  min-width: 150px;
  border-right: 1px solid #e0e0e0;
  padding: 8px;
  font-weight: 500;
}

.timeline-track-header {
  flex: 1;
  min-width: 180px;
  padding: 8px;
  border-right: 1px solid #e0e0e0;
}

.track-header-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.track-header-content i {
  font-size: 0.9rem;
  opacity: 0.7;
}

.timeline-content {
  display: flex;
  flex-grow: 1;
  overflow: auto;
  position: relative;
}

.timeline-scale {
  width: 150px;
  min-width: 150px;
  height: 100%;
  border-right: 1px solid #e0e0e0;
  background-color: #f9f9f9;
  position: sticky;
  left: 0;
  z-index: 2;
}

.timeline-track {
  flex: 1;
  min-width: 180px;
  border-right: 1px solid #e0e0e0;
  border-bottom: 1px solid #e0e0e0;
  position: relative;
  min-height: 80px;
}

.timeline-tick {
  position: absolute;
  top: 0;
  height: 20px;
}

.tick-line {
  position: absolute;
  top: 0;
  height: 6px;
  border-left: 1px solid #ccc;
}

.tick-label {
  position: absolute;
  top: 10px;
  left: 2px;
  font-size: 0.8rem;
  color: #666;
  white-space: nowrap;
}

.timeline-item {
  position: absolute;
  height: 60px;
  top: 10px;
  background-color: #BBDEFB;
  border-radius: 4px;
  padding: 4px 8px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transition: all 0.2s ease;
}

.timeline-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 3px 6px rgba(0,0,0,0.15);
}

.item-selected {
  box-shadow: 0 0 0 2px #333, 0 4px 8px rgba(0,0,0,0.2);
  z-index: 1;
}

.item-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.item-title {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.9rem;
}

.item-details {
  position: absolute;
  right: 16px;
  top: 68px;
  width: 300px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  z-index: 1000;
  max-height: calc(100% - 88px);
  display: flex;
  flex-direction: column;
}

.item-details-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  padding: 12px 16px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
}

.item-type {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  color: #666;
  margin-right: auto;
}

.item-details-header h3 {
  flex: 1 0 100%;
  margin: 8px 0 0 0;
  font-size: 1.2rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  opacity: 0.7;
  line-height: 1;
  padding: 0;
  margin-left: 8px;
}

.close-btn:hover {
  opacity: 1;
}

.item-details-content {
  padding: 16px;
  overflow-y: auto;
  flex-grow: 1;
}

.item-details-section {
  margin-bottom: 16px;
}

.item-details-section h4 {
  margin: 0 0 8px 0;
  font-size: 1rem;
  color: #666;
  border-bottom: 1px solid #eee;
  padding-bottom: 4px;
}

.item-metadata {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 4px 8px;
  margin: 0;
}

.item-metadata dt {
  font-weight: 500;
  color: #666;
}

.item-metadata dd {
  margin: 0;
}

.item-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
}

.action-btn {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  background-color: #f5f5f5;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
}

.action-btn:hover {
  background-color: #e0e0e0;
}