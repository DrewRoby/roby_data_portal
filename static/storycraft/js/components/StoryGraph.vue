<template>
  <div class="story-graph-container">
    <div class="graph-controls">
      <div class="filter-buttons">
        <button 
          v-for="(active, type) in filters" 
          :key="type"
          :class="['filter-btn', type.toLowerCase(), { active }]"
          @click="toggleFilter(type)"
        >
          <i :class="getIconClass(type)"></i>
          {{ type }}
        </button>
      </div>
      <div class="zoom-controls">
        <button @click="zoom(0.2)" class="zoom-btn">
          <i class="fas fa-search-plus"></i>
        </button>
        <button @click="zoom(-0.2)" class="zoom-btn">
          <i class="fas fa-search-minus"></i>
        </button>
        <button @click="resetZoom()" class="zoom-btn">
          <i class="fas fa-expand"></i>
        </button>
      </div>
    </div>
    
    <div class="graph-container" ref="graphContainer">
      <!-- Graph will be rendered here by D3.js -->
      <div v-if="loading" class="graph-loading">
        <div class="spinner"></div>
        <p>Building story network...</p>
      </div>
    </div>
    
    <div class="entity-details" v-if="selectedEntity">
      <div class="entity-header" :class="selectedEntity.type.toLowerCase()">
        <i :class="getIconClass(selectedEntity.type)"></i>
        <h3>{{ selectedEntity.name }}</h3>
        <button class="close-btn" @click="closeDetails">×</button>
      </div>
      <div class="entity-content">
        <p v-if="selectedEntity.description">{{ selectedEntity.description }}</p>
        
        <div v-if="selectedEntity.type === 'Character'" class="entity-relationships">
          <h4>Appears in:</h4>
          <ul>
            <li v-for="scene in relatedScenes" :key="scene.id" 
                @click="selectEntity(scene)" class="related-entity">
              {{ scene.name }}
            </li>
          </ul>
          
          <h4>Relationships:</h4>
          <ul>
            <li v-for="rel in characterRelationships" :key="rel.id" class="relationship-item">
              <span @click="selectEntity(rel.character)" class="related-entity">
                {{ rel.character.name }}
              </span> - {{ rel.relationship }}
            </li>
          </ul>
        </div>
        
        <div v-if="selectedEntity.type === 'Setting'" class="entity-scenes">
          <h4>Scenes that take place here:</h4>
          <ul>
            <li v-for="scene in relatedScenes" :key="scene.id" 
                @click="selectEntity(scene)" class="related-entity">
              {{ scene.name }}
            </li>
          </ul>
        </div>
        
        <div v-if="selectedEntity.type === 'Scene'" class="entity-components">
          <h4>Setting:</h4>
          <p @click="selectEntity(selectedEntity.setting)" class="related-entity">
            {{ selectedEntity.setting ? selectedEntity.setting.name : 'None assigned' }}
          </p>
          
          <h4>Characters in this scene:</h4>
          <ul>
            <li v-for="character in sceneCharacters" :key="character.id" 
                @click="selectEntity(character)" class="related-entity">
              {{ character.name }}
            </li>
          </ul>
        </div>
        
        <div class="entity-actions">
          <button @click="editEntity(selectedEntity)" class="action-btn">
            <i class="fas fa-edit"></i> Edit
          </button>
          <button v-if="selectedEntity.type !== 'Story'" 
                  @click="removeEntity(selectedEntity)" class="action-btn danger">
            <i class="fas fa-trash"></i> Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as d3 from 'd3';

export default {
  name: 'StoryGraph',
  props: {
    storyId: {
      type: Number,
      required: true
    }
  },
  data() {
    return {
      loading: true,
      storyData: null,
      simulation: null,
      svg: null,
      nodes: [],
      links: [],
      filters: {
        'Character': true,
        'Setting': true,
        'Scene': true,
        'Plot': true
      },
      selectedEntity: null,
      transform: {
        scale: 1,
        x: 0,
        y: 0
      }
    };
  },
  computed: {
    relatedScenes() {
      if (!this.selectedEntity || !this.storyData) return [];
      
      if (this.selectedEntity.type === 'Character') {
        return this.storyData.scenes.filter(scene => 
          scene.characters.includes(this.selectedEntity.id)
        );
      } else if (this.selectedEntity.type === 'Setting') {
        return this.storyData.scenes.filter(scene => 
          scene.setting_id === this.selectedEntity.id
        );
      }
      
      return [];
    },
    characterRelationships() {
      if (!this.selectedEntity || this.selectedEntity.type !== 'Character' || !this.storyData) 
        return [];
      
      return this.storyData.relationships.filter(rel => 
        rel.source_id === this.selectedEntity.id || rel.target_id === this.selectedEntity.id
      ).map(rel => {
        const otherCharId = rel.source_id === this.selectedEntity.id ? rel.target_id : rel.source_id;
        const character = this.storyData.characters.find(c => c.id === otherCharId);
        
        return {
          id: rel.id,
          relationship: rel.relationship,
          character: character
        };
      });
    },
    sceneCharacters() {
      if (!this.selectedEntity || this.selectedEntity.type !== 'Scene' || !this.storyData) 
        return [];
      
      return this.storyData.characters.filter(character => 
        this.selectedEntity.characters.includes(character.id)
      );
    }
  },
  mounted() {
    this.fetchStoryData();
    window.addEventListener('resize', this.resizeGraph);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resizeGraph);
    if (this.simulation) {
      this.simulation.stop();
    }
  },
  methods: {
    async fetchStoryData() {
      this.loading = true;
      try {
        // In a real implementation, this would be an API call
        // For now, we'll simulate a network request with a timeout
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Mock data structure - in production this would come from your API
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
            { id: a1, type: 'Plot', name: 'Main Quest', description: 'The primary story arc' }
          ],
          scenes: [
            { 
              id: 1, 
              type: 'Scene', 
              name: 'The Call', 
              description: 'Elara receives a mysterious message',
              setting_id: 1,
              plot_id: 1,
              characters: [1]
            },
            { 
              id: 2, 
              type: 'Scene', 
              name: 'The Meeting', 
              description: 'Elara meets her mentor Kaden',
              setting_id: 1,
              plot_id: 1,
              characters: [1, 2]
            },
            { 
              id: 3, 
              type: 'Scene', 
              name: 'The Confrontation', 
              description: 'Elara confronts Vex at the temple',
              setting_id: 3,
              plot_id: 1,
              characters: [1, 3]
            },
            { 
              id: 4, 
              type: 'Scene', 
              name: 'The Summit', 
              description: 'Final battle at the mountain peak',
              setting_id: 2,
              plot_id: 1,
              characters: [1, 2, 3]
            }
          ],
          relationships: [
            { id: 1, source_id: 1, target_id: 2, relationship: 'Mentee/Mentor' },
            { id: 2, source_id: 1, target_id: 3, relationship: 'Enemy' },
            { id: 3, source_id: 2, target_id: 3, relationship: 'Old Rivals' }
          ]
        };
        
        this.buildGraphData();
        this.initGraph();
        this.loading = false;
      } catch (error) {
        console.error('Error fetching story data:', error);
        this.loading = false;
      }
    },
    buildGraphData() {
      // Create nodes array from all entities
      this.nodes = [
        ...this.storyData.characters,
        ...this.storyData.settings,
        ...this.storyData.plots,
        ...this.storyData.scenes
      ];
      
      // Create links array
      this.links = [];
      
      // Scene to Setting links
      this.storyData.scenes.forEach(scene => {
        if (scene.setting_id) {
          this.links.push({
            source: scene.id,
            target: scene.setting_id,
            type: 'scene_setting'
          });
        }
      });
      
      // Scene to Character links
      this.storyData.scenes.forEach(scene => {
        scene.characters.forEach(charId => {
          this.links.push({
            source: scene.id,
            target: charId,
            type: 'scene_character'
          });
        });
      });
      
      // Scene to Plot links
      this.storyData.scenes.forEach(scene => {
        if (scene.plot_id) {
          this.links.push({
            source: scene.id,
            target: scene.plot_id,
            type: 'scene_plot'
          });
        }
      });
      
      // Character to Character relationship links
      this.storyData.relationships.forEach(rel => {
        this.links.push({
          source: rel.source_id,
          target: rel.target_id,
          type: 'character_relationship',
          label: rel.relationship
        });
      });
    },
    initGraph() {
      const container = this.$refs.graphContainer;
      const width = container.clientWidth;
      const height = container.clientHeight;
      
      // Create SVG element
      this.svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', [0, 0, width, height])
        .call(d3.zoom()
          .scaleExtent([0.1, 3])
          .on('zoom', (event) => {
            this.transform = event.transform;
            g.attr('transform', event.transform);
          }));
      
      // Main group element for zoom/pan
      const g = this.svg.append('g');
      
      // Define markers for arrows
      this.svg.append('defs').selectAll('marker')
        .data(['relationship'])
        .enter().append('marker')
        .attr('id', d => `arrow-${d}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 25)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('fill', '#999')
        .attr('d', 'M0,-5L10,0L0,5');
      
      // Create links
      const link = g.append('g')
        .selectAll('line')
        .data(this.links)
        .enter()
        .append('line')
        .attr('class', d => `link ${d.type}`)
        .attr('stroke', this.getLinkColor)
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', 1.5)
        .attr('marker-end', d => d.type === 'character_relationship' ? 'url(#arrow-relationship)' : null);
      
      // Link labels for relationships
      const linkLabels = g.append('g')
        .selectAll('text')
        .data(this.links.filter(d => d.label))
        .enter()
        .append('text')
        .attr('class', 'link-label')
        .text(d => d.label)
        .attr('font-size', 8)
        .attr('text-anchor', 'middle')
        .attr('dy', -5);
      
      // Create nodes
      const node = g.append('g')
        .selectAll('g')
        .data(this.nodes)
        .enter()
        .append('g')
        .attr('class', d => `node ${d.type.toLowerCase()}`)
        .call(d3.drag()
          .on('start', this.dragstarted)
          .on('drag', this.dragged)
          .on('end', this.dragended));
      
      // Node circles
      node.append('circle')
        .attr('r', d => this.getNodeRadius(d))
        .attr('fill', d => this.getNodeColor(d))
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5);
      
      // Node labels
      node.append('text')
        .text(d => d.name)
        .attr('x', 0)
        .attr('y', d => this.getNodeRadius(d) + 10)
        .attr('text-anchor', 'middle')
        .attr('font-size', 10);
      
      // Node interaction
      node.on('click', (event, d) => {
        event.stopPropagation();
        this.selectEntity(d);
      });
      
      // Background click to deselect
      this.svg.on('click', () => {
        this.selectedEntity = null;
      });
      
      // Set up force simulation
      this.simulation = d3.forceSimulation(this.nodes)
        .force('link', d3.forceLink(this.links)
          .id(d => d.id)
          .distance(80))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => this.getNodeRadius(d) + 5))
        .on('tick', () => {
          link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
          
          linkLabels
            .attr('x', d => (d.source.x + d.target.x) / 2)
            .attr('y', d => (d.source.y + d.target.y) / 2);
          
          node
            .attr('transform', d => `translate(${d.x}, ${d.y})`);
        });
    },
    toggleFilter(type) {
      this.filters[type] = !this.filters[type];
      this.updateVisibility();
    },
    updateVisibility() {
      // Update node visibility
      this.svg.selectAll('.node')
        .style('display', d => this.filters[d.type] ? 'block' : 'none');
      
      // Update link visibility based on connected nodes
      this.svg.selectAll('.link')
        .style('display', d => {
          const sourceNode = this.nodes.find(n => n.id === d.source.id || n.id === d.source);
          const targetNode = this.nodes.find(n => n.id === d.target.id || n.id === d.target);
          
          return (sourceNode && targetNode && 
                  this.filters[sourceNode.type] && 
                  this.filters[targetNode.type]) ? 'block' : 'none';
        });
      
      // Update link labels
      this.svg.selectAll('.link-label')
        .style('display', d => {
          const sourceNode = this.nodes.find(n => n.id === d.source.id || n.id === d.source);
          const targetNode = this.nodes.find(n => n.id === d.target.id || n.id === d.target);
          
          return (sourceNode && targetNode && 
                  this.filters[sourceNode.type] && 
                  this.filters[targetNode.type]) ? 'block' : 'none';
        });
    },
    getNodeRadius(node) {
      switch (node.type) {
        case 'Character': return 15;
        case 'Setting': return 12;
        case 'Scene': return 10;
        case 'Plot': return 20;
        default: return 8;
      }
    },
    getNodeColor(node) {
      switch (node.type) {
        case 'Character': return '#4285F4'; // Blue
        case 'Setting': return '#34A853';   // Green
        case 'Scene': return '#FBBC05';     // Yellow
        case 'Plot': return '#EA4335';      // Red
        default: return '#9AA0A6';          // Gray
      }
    },
    getLinkColor(link) {
      switch (link.type) {
        case 'scene_character': return '#4285F4';
        case 'scene_setting': return '#34A853';
        case 'scene_plot': return '#EA4335';
        case 'character_relationship': return '#9C27B0';
        default: return '#9AA0A6';
      }
    },
    getIconClass(type) {
      switch (type) {
        case 'Character': return 'fas fa-user';
        case 'Setting': return 'fas fa-map-marker-alt';
        case 'Scene': return 'fas fa-file-alt';
        case 'Plot': return 'fas fa-project-diagram';
        default: return 'fas fa-circle';
      }
    },
    selectEntity(entity) {
      this.selectedEntity = entity;
    },
    closeDetails() {
      this.selectedEntity = null;
    },
    editEntity(entity) {
      // This would open an edit modal or redirect to an edit page
      this.$emit('edit-entity', entity);
    },
    removeEntity(entity) {
      if (confirm(`Are you sure you want to delete ${entity.name}?`)) {
        this.$emit('remove-entity', entity);
      }
    },
    dragstarted(event, d) {
      if (!event.active) this.simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    },
    dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    },
    dragended(event, d) {
      if (!event.active) this.simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    },
    zoom(delta) {
      const container = this.$refs.graphContainer;
      const width = container.clientWidth;
      const height = container.clientHeight;
      
      // Get current transform
      const transform = this.transform;
      
      // Calculate new scale
      const newScale = Math.max(0.1, Math.min(3, transform.scale + delta));
      
      // Apply new zoom transform
      const newTransform = d3.zoomIdentity
        .translate(transform.x, transform.y)
        .scale(newScale);
      
      // Apply the zoom transform
      this.svg.call(
        d3.zoom().transform,
        newTransform
      );
    },
    resetZoom() {
      this.svg.call(
        d3.zoom().transform,
        d3.zoomIdentity
      );
    },
    resizeGraph() {
      if (!this.svg) return;
      
      const container = this.$refs.graphContainer;
      const width = container.clientWidth;
      const height = container.clientHeight;
      
      this.svg
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', [0, 0, width, height]);
      
      // Restart simulation with new center
      this.simulation
        .force('center', d3.forceCenter(width / 2, height / 2))
        .alpha(0.3)
        .restart();
    }
  }
};
</script>

<style scoped>
.story-graph-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}

.graph-controls {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
}

.filter-buttons {
  display: flex;
  gap: 8px;
}

.filter-btn {
  padding: 5px 10px;
  border: none;
  border-radius: 4px;
  background-color: #e0e0e0;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.9rem;
}

.filter-btn i {
  font-size: 0.8rem;
}

.filter-btn.active {
  background-color: #333;
  color: white;
}

.filter-btn.character.active {
  background-color: #4285F4;
}

.filter-btn.setting.active {
  background-color: #34A853;
}

.filter-btn.scene.active {
  background-color: #FBBC05;
  color: #333;
}

.filter-btn.plot.active {
  background-color: #EA4335;
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

.graph-container {
  flex-grow: 1;
  position: relative;
  overflow: hidden;
  min-height: 500px;
}

.graph-loading {
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

.entity-details {
  position: absolute;
  right: 16px;
  top: 60px;
  width: 300px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  z-index: 1000;
  max-height: calc(100% - 80px);
  display: flex;
  flex-direction: column;
}

.entity-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
}

.entity-header.character {
  background-color: #4285F4;
  color: white;
}

.entity-header.setting {
  background-color: #34A853;
  color: white;
}

.entity-header.scene {
  background-color: #FBBC05;
  color: #333;
}

.entity-header.plot {
  background-color: #EA4335;
  color: white;
}

.entity-header i {
  margin-right: 8px;
}

.entity-header h3 {
  flex-grow: 1;
  margin: 0;
  font-size: 1.1rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: inherit;
  opacity: 0.7;
}

.close-btn:hover {
  opacity: 1;
}

.entity-content {
  padding: 16px;
  overflow-y: auto;
  flex-grow: 1;
}

.entity-relationships h4,
.entity-scenes h4,
.entity-components h4 {
  margin: 16px 0 8px;
  font-size: 1rem;
  color: #666;
}

.related-entity {
  color: #4285F4;
  cursor: pointer;
  text-decoration: underline;
}

.relationship-item {
  margin-bottom: 4px;
}

.entity-actions {
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

.action-btn.danger {
  color: #EA4335;
}

.action-btn.danger:hover {
  background-color: #ffebee;
}

/* D3 styling */
:deep(.link) {
  stroke-opacity: 0.6;
}

:deep(.link-label) {
  fill: #666;
  pointer-events: none;
}

:deep(.node text) {
  fill: #333;
  pointer-events: none;
}

:deep(.node:hover circle) {
  stroke: #333;
  stroke-width: 2px;
}
</style>