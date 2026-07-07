"""Knowledge Graph over ERP entities.

A lightweight in-DB graph: nodes are ERP records (customer, supplier,
item, order, project), edges are typed relationships (supplies, ordered,
belongs_to). Enables questions like "what does this delay affect?" by
traversing relationships. Backed by simple tables so it needs no extra
graph-DB service; can be swapped for Neo4j later behind the same API.
"""
from django.db import models


class GraphNode(models.Model):
    node_type = models.CharField(max_length=50, db_index=True)
    ref_id = models.CharField(max_length=64, db_index=True)
    label = models.CharField(max_length=255)
    company_id = models.IntegerField(null=True, db_index=True)
    attributes = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'core'
        unique_together = [('node_type', 'ref_id')]

    def __str__(self):
        return f"{self.node_type}:{self.label}"


class GraphEdge(models.Model):
    source = models.ForeignKey(GraphNode, on_delete=models.CASCADE,
                               related_name='out_edges')
    target = models.ForeignKey(GraphNode, on_delete=models.CASCADE,
                               related_name='in_edges')
    relation = models.CharField(max_length=50, db_index=True)
    weight = models.FloatField(default=1.0)
    attributes = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'core'
        unique_together = [('source', 'target', 'relation')]


class KnowledgeGraph:
    def upsert_node(self, node_type, ref_id, label, company_id=None, **attrs):
        node, _ = GraphNode.objects.update_or_create(
            node_type=node_type, ref_id=str(ref_id),
            defaults={'label': label, 'company_id': company_id,
                      'attributes': attrs})
        return node

    def link(self, source, target, relation, weight=1.0, **attrs):
        edge, _ = GraphEdge.objects.update_or_create(
            source=source, target=target, relation=relation,
            defaults={'weight': weight, 'attributes': attrs})
        return edge

    def neighbors(self, node, relation=None, direction='out'):
        edges = (node.out_edges if direction == 'out' else node.in_edges).all()
        if relation:
            edges = edges.filter(relation=relation)
        other = 'target' if direction == 'out' else 'source'
        return [getattr(e, other) for e in edges.select_related(other)]

    def impact_of(self, node, max_depth: int = 3) -> list[dict]:
        """BFS downstream: what does a change to `node` affect?"""
        seen, frontier, out = {node.pk}, [(node, 0)], []
        while frontier:
            cur, depth = frontier.pop(0)
            if depth >= max_depth:
                continue
            for e in cur.out_edges.select_related('target'):
                t = e.target
                if t.pk not in seen:
                    seen.add(t.pk)
                    out.append({'node': str(t), 'type': t.node_type,
                                'relation': e.relation, 'depth': depth + 1})
                    frontier.append((t, depth + 1))
        return out


graph = KnowledgeGraph()
