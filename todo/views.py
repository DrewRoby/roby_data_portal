from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages
from .models import Board, Task, Project
from .forms import BoardForm, TaskForm, ProjectForm

def get_todo_nav_context(active_tab='boards'):
    """Return navigation context for Todo templates"""
    nav_tabs = [
        {'name': 'Boards', 'url': 'todo:board_list', 'icon': 'fa-clipboard-list'},
        {'name': 'Projects', 'url': 'todo:project_list', 'icon': 'fa-project-diagram'},
    ]
    
    return {
        'nav_tabs': nav_tabs,
        'active_tab': active_tab
    }

def board_list(request):
    boards = Board.objects.filter(user=request.user)

    # If there are no boards, create a default one
    if not boards.exists():
        default_board = Board.objects.create(
            name="My First Board",
            user=request.user
        )
        boards = [default_board]
    
    # Get navigation context
    context = get_todo_nav_context(active_tab='Boards')
    
    # Add view-specific context
    context.update({
        'boards': boards,
    })

    return render(request, 'todo/board_list.html', context)


def board_detail(request, board_id):
    board = get_object_or_404(Board, id=board_id, user=request.user)
    boards = Board.objects.filter(user=request.user)
    projects = Project.objects.filter(user=request.user)

    # Get tasks for each status
    todo_tasks = Task.objects.filter(board=board, status='todo', user=request.user)
    in_progress_tasks = Task.objects.filter(board=board, status='in_progress', user=request.user)
    done_tasks = Task.objects.filter(board=board, status='done', user=request.user)

    # Forms
    task_form = TaskForm(user=request.user)
    
    # Get navigation context
    context = get_todo_nav_context(active_tab='Boards')
    
    # Add board-specific actions
    board_actions = [
        {'name': 'Add Task', 'url': 'todo:create_task', 'url_params': [board.id], 'icon': 'fa-plus'}
    ]
    
    # Add view-specific context
    context.update({
        'board': board,
        'boards': boards,
        'projects': projects,
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'done_tasks': done_tasks,
        'task_form': task_form,
        'board_actions': board_actions,
    })

    return render(request, 'todo/board_detail.html', context)


def create_board(request):
    if request.method == 'POST':
        form = BoardForm(request.POST)
        if form.is_valid():
            board = form.save(commit=False)
            board.user = request.user
            board.save()
            return redirect('todo:board_detail', board_id=board.id)
    else:
        form = BoardForm()

    return render(request, 'todo/create_board.html', {'form': form})


def delete_board(request, board_id):
    board = get_object_or_404(Board, id=board_id, user=request.user)
    
    if request.method == 'POST':
        board_name = board.name
        board.delete()
        messages.success(request, f'Board "{board_name}" has been deleted.')
        return redirect('todo:board_list')
    
    # If someone tries to access this via GET, redirect to board list
    return redirect('todo:board_list')


def create_task(request, board_id):
    board = get_object_or_404(Board, id=board_id, user=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.board = board
            task.save()
            return redirect('todo:board_detail', board_id=board.id)
    else:
        form = TaskForm(user=request.user)

    return render(request, 'todo/create_task.html', {'form': form, 'board': board})


def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    board_id = task.board.id

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('todo:board_detail', board_id=board_id)
    else:
        form = TaskForm(instance=task, user=request.user)

    return render(request, 'todo/edit_task.html', {'form': form, 'task': task})


@require_POST
def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)

    status = request.POST.get('status')
    if status in dict(Task.STATUS_CHOICES).keys():
        task.status = status
        task.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid status'})


def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            return redirect('todo:board_list')
    else:
        form = ProjectForm()

    return render(request, 'todo/create_project.html', {'form': form})


def project_list(request):
    projects = Project.objects.filter(user=request.user)
    
    # Get navigation context
    context = get_todo_nav_context(active_tab='Projects')
    
    # Add view-specific context
    context.update({
        'projects': projects,
    })

    return render(request, 'todo/project_list.html', context)