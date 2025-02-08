from django.core.files.storage import FileSystemStorage
from django.http import FileResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.conf import settings
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Project, Comment, Citation, ResearchSection
from .forms import ProjectForm, CommentForm, CitationForm


def project_list(request):
    """List all research projects."""
    projects = Project.objects.all()
    context = {'projects': projects}
    return render(request, 'marketplace/project_list.html', context)




def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    comments = project.comments.all()
    citations = project.citations.all()
    related_projects = project.related_projects.all()

    if request.method == 'POST':
        # Handling Comment submission
        if 'comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.project = project
                comment.user = request.user
                comment.save()
                return redirect('project_detail', project_id=project.id)

        # Handling Citation submission
        elif 'citation' in request.POST:
            citation_form = CitationForm(request.POST)
            if citation_form.is_valid():
                citation = citation_form.save(commit=False)
                citation.project = project
                citation.save()
                return redirect('project_detail', project_id=project.id)
    else:
        comment_form = CommentForm()
        citation_form = CitationForm()

    return render(request, 'marketplace/project_detail.html', {
        'project': project,
        'comments': comments,
        'citations': citations,
        'related_projects': related_projects,
        'comment_form': comment_form,
        'citation_form': citation_form,
    })






@login_required
def project_create(request):
    if request.method == 'POST':
        project_form = ProjectForm(request.POST, request.FILES)

        if project_form.is_valid():
            # Create the project
            project = project_form.save()

            # Handle dynamic research sections
            section_titles = request.POST.getlist('section_title[]')
            section_contents = request.POST.getlist('section_content[]')

            for title, content in zip(section_titles, section_contents):
                ResearchSection.objects.create(
                    project=project,
                    title=title,
                    content=content
                )

            return redirect('project_detail', project.id)
    else:
        project_form = ProjectForm()

    return render(request, 'marketplace/project_create.html', {'form': project_form})


@login_required
def project_edit(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.user != project.owner:
        return redirect('project_detail', project_id=project.id)  # Prevent non-owners from editing

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            form.save_m2m()  # Save many-to-many relationships
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project)

    return render(request, 'project_edit.html', {
        'form': form,
        'project': project
    })

@login_required
def project_delete(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.user == project.owner:
        project.delete()
        return redirect('project_list')  # Redirect to a list of all projects after deletion
    return redirect('project_detail', project_id=project.id)
