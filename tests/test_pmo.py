import pytest
from apps.projects.models import Project, Milestone, RiskRegister, IssueLog, ChangeRequest


@pytest.mark.django_db
class TestProjectProgress:
    def test_progress_percent_computed_from_tasks(self, authenticated_client, company):
        project = Project.objects.create(company=company, project_name='P1', project_code='P1', budget=10000)
        resp = authenticated_client.get(f'/api/v1/projects/{project.id}/')
        assert resp.data['progress_percent'] == 0  # no tasks yet

        authenticated_client.post('/api/v1/projects/tasks/', {'project': project.id, 'subject': 'T1', 'status': 'Completed'})
        authenticated_client.post('/api/v1/projects/tasks/', {'project': project.id, 'subject': 'T2', 'status': 'Open'})

        resp = authenticated_client.get(f'/api/v1/projects/{project.id}/')
        assert resp.data['progress_percent'] == 50.0

    def test_budget_variance_computed(self, authenticated_client, company):
        project = Project.objects.create(company=company, project_name='P2', project_code='P2', budget=10000, actual_cost=6000)
        resp = authenticated_client.get(f'/api/v1/projects/{project.id}/')
        assert float(resp.data['budget_variance']) == 4000.0


@pytest.mark.django_db
class TestMilestone:
    def test_overdue_flag(self, authenticated_client, company):
        project = Project.objects.create(company=company, project_name='P3', project_code='P3')
        overdue = Milestone.objects.create(project=project, name='Late one', due_date='2020-01-01')
        future = Milestone.objects.create(project=project, name='Future one', due_date='2030-01-01')

        resp = authenticated_client.get(f'/api/v1/projects/milestones/{overdue.id}/')
        assert resp.data['is_overdue'] is True

        resp = authenticated_client.get(f'/api/v1/projects/milestones/{future.id}/')
        assert resp.data['is_overdue'] is False


@pytest.mark.django_db
class TestRiskRegister:
    def test_risk_score_and_level(self, authenticated_client, company):
        project = Project.objects.create(company=company, project_name='P4', project_code='P4')
        resp = authenticated_client.post('/api/v1/projects/risks/', {
            'project': project.id, 'title': 'Vendor delay', 'probability': 4, 'impact': 5,
        })
        assert resp.status_code == 201
        assert resp.data['risk_score'] == 20
        assert resp.data['risk_level'] == 'Critical'

    def test_low_risk_level(self, authenticated_client, company):
        project = Project.objects.create(company=company, project_name='P5', project_code='P5')
        resp = authenticated_client.post('/api/v1/projects/risks/', {
            'project': project.id, 'title': 'Minor risk', 'probability': 1, 'impact': 2,
        })
        assert resp.data['risk_score'] == 2
        assert resp.data['risk_level'] == 'Low'


@pytest.mark.django_db
class TestChangeRequestWorkflow:
    def test_cannot_skip_pending_to_implemented(self, authenticated_client, company):
        project = Project.objects.create(company=company, project_name='P6', project_code='P6')
        cr = authenticated_client.post('/api/v1/projects/change-requests/', {
            'project': project.id, 'title': 'Scope increase',
        }).data
        resp = authenticated_client.patch(f'/api/v1/projects/change-requests/{cr["id"]}/', {'status': 'Implemented'})
        assert resp.status_code == 400

    def test_valid_transition_path(self, authenticated_client, company):
        project = Project.objects.create(company=company, project_name='P7', project_code='P7')
        cr = authenticated_client.post('/api/v1/projects/change-requests/', {
            'project': project.id, 'title': 'Scope increase 2',
        }).data
        resp1 = authenticated_client.patch(f'/api/v1/projects/change-requests/{cr["id"]}/', {'status': 'Approved'})
        assert resp1.status_code == 200
        resp2 = authenticated_client.patch(f'/api/v1/projects/change-requests/{cr["id"]}/', {'status': 'Implemented'})
        assert resp2.status_code == 200

    def test_rejected_is_final(self, authenticated_client, company):
        project = Project.objects.create(company=company, project_name='P8', project_code='P8')
        cr = authenticated_client.post('/api/v1/projects/change-requests/', {
            'project': project.id, 'title': 'Scope increase 3',
        }).data
        authenticated_client.patch(f'/api/v1/projects/change-requests/{cr["id"]}/', {'status': 'Rejected'})
        resp = authenticated_client.patch(f'/api/v1/projects/change-requests/{cr["id"]}/', {'status': 'Approved'})
        assert resp.status_code == 400


@pytest.mark.django_db
class TestIssueLogAndStakeholders:
    def test_create_issue(self, authenticated_client, company):
        project = Project.objects.create(company=company, project_name='P9', project_code='P9')
        resp = authenticated_client.post('/api/v1/projects/issues/', {
            'project': project.id, 'title': 'Server down', 'severity': 'Critical',
        })
        assert resp.status_code == 201
        assert resp.data['status'] == 'Open'

    def test_create_stakeholder(self, authenticated_client, company):
        project = Project.objects.create(company=company, project_name='P10', project_code='P10')
        resp = authenticated_client.post('/api/v1/projects/stakeholders/', {
            'project': project.id, 'name': 'Sponsor', 'influence': 'High', 'interest': 'High',
        })
        assert resp.status_code == 201


@pytest.mark.django_db
class TestTaskDependencies:
    def test_task_can_depend_on_another(self, authenticated_client, company):
        project = Project.objects.create(company=company, project_name='P11', project_code='P11')
        t1 = authenticated_client.post('/api/v1/projects/tasks/', {'project': project.id, 'subject': 'Foundation'}).data
        t2 = authenticated_client.post('/api/v1/projects/tasks/', {'project': project.id, 'subject': 'Walls'}).data
        resp = authenticated_client.patch(f'/api/v1/projects/tasks/{t2["id"]}/', {'depends_on': [t1['id']]})
        assert resp.status_code == 200
        assert t1['id'] in resp.data['depends_on']
