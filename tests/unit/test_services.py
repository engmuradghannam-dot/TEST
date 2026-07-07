import pytest
from apps.core.services.base import BaseService, BaseRepository, DomainEvent, EventBus


class MockRepository(BaseRepository):
    def __init__(self):
        self.data = {}
        self.next_id = 1

    def get(self, id):
        return self.data.get(id)

    def list(self, filters=None):
        return list(self.data.values())

    def create(self, data):
        item = {'id': self.next_id, **data}
        self.data[self.next_id] = item
        self.next_id += 1
        return item

    def update(self, id, data):
        if id in self.data:
            self.data[id].update(data)
            return self.data[id]
        return None

    def delete(self, id):
        return self.data.pop(id, None) is not None


@pytest.mark.django_db
class TestBaseService:
    def test_create(self):
        repo = MockRepository()
        service = BaseService(repo)
        result = service.create({'name': 'Test'})
        assert result['name'] == 'Test'
        assert result['id'] == 1

    def test_get(self):
        repo = MockRepository()
        service = BaseService(repo)
        created = service.create({'name': 'Test'})
        result = service.get(created['id'])
        assert result['name'] == 'Test'

    def test_list(self):
        repo = MockRepository()
        service = BaseService(repo)
        service.create({'name': 'A'})
        service.create({'name': 'B'})
        results = service.list()
        assert len(results) == 2


class TestEventBus:
    def test_publish_subscribe(self):
        events = []
        def handler(event):
            events.append(event)

        EventBus.subscribe('test_event', handler)
        event = DomainEvent('test_event', 1, {'data': 'test'})
        EventBus.publish(event)

        assert len(events) == 1
        assert events[0].event_type == 'test_event'
