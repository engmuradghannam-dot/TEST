import pytest
from apps.projects.models import Project, Task


@pytest.mark.django_db
class TestTeamTaskVisibility:
    def test_employee_sees_personal_and_team_tasks_only(
        self, api_client, company, company_user, employee, employee2, team
    ):
        project = Project.objects.create(company=company, project_name='Proj', project_code='P1')
        personal_task = Task.objects.create(project=project, subject='Personal for Sara', assigned_to=employee)
        team_task = Task.objects.create(project=project, subject='Team task', team=team)
        other_task = Task.objects.create(project=project, subject='Only Omar', assigned_to=employee2)

        api_client.force_authenticate(user=company_user)
        resp = api_client.get('/api/v1/projects/tasks/')
        assert resp.status_code == 200
        subjects = {t['subject'] for t in resp.data['results']}

        assert personal_task.subject in subjects
        assert team_task.subject in subjects
        assert other_task.subject not in subjects

    def test_staff_sees_all_company_tasks(self, authenticated_client, company, employee, employee2):
        project = Project.objects.create(company=company, project_name='Proj2', project_code='P2')
        Task.objects.create(project=project, subject='Task A', assigned_to=employee)
        Task.objects.create(project=project, subject='Task B', assigned_to=employee2)

        resp = authenticated_client.get('/api/v1/projects/tasks/')
        assert resp.status_code == 200
        assert len(resp.data['results']) == 2
