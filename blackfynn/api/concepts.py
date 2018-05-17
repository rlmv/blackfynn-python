# -*- coding: utf-8 -*-
from blackfynn.api.base import APIBase
from blackfynn.models import (
    Concept, ConceptInstance, ConceptInstanceSet, ConceptProperty, ProxyInstance,
    Relationship, RelationshipInstance, RelationshipInstanceSet, RelationshipProperty,
    DataPackage
)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Concepts
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ConceptsAPIBase(APIBase):

    def _get_concept_type(self, concept, instance = None):
        if isinstance(concept, Concept):
            return concept.type
        elif isinstance(concept, basestring):
            return concept
        elif isinstance(instance, ConceptInstance):
            return instance.type
        else:
            raise Exception("could not get concept type from concept {} or instance {} ".format(concept, instance))

    def _get_relationship_type(self, relationship, instance = None):
        if isinstance(relationship, Relationship):
            return relationship.type
        elif isinstance(relationship, basestring):
            return relationship
        elif isinstance(instance, RelationshipInstance):
            return instance.type
        else:
            raise Exception("could not get relationship type from relationship {} or instance {} ".format(relationship, instance))

class ConceptsAPI(ConceptsAPIBase):
    base_uri = "/datasets"
    name = 'concepts'

    def __init__(self, session):
        self.host = session._concepts_host
        self.instances = ConceptInstancesAPI(session)
        self.relationships = ConceptRelationshipsAPI(session)
        self.proxies = ConceptProxiesAPI(session)
        super(ConceptsAPI, self).__init__(session)

    def get_properties(self, dataset, concept):
        dataset_id = self._get_id(dataset)
        concept_id = self._get_id(concept)
        resp = self._get(self._uri('/{dataset_id}/concepts/{id}/properties', dataset_id=dataset_id, id=concept_id))
        return [ConceptProperty.from_dict(r) for r in resp]

    def update_properties(self, dataset, concept):
        assert isinstance(concept, Concept), "concept must be type Concept"
        assert concept.schema, "concept schema cannot be empty"
        data = concept.as_dict()['schema']
        dataset_id = self._get_id(dataset)
        resp = self._put(self._uri('/{dataset_id}/concepts/{id}/properties', dataset_id=dataset_id, id=concept.id), json=data)
        return [ConceptProperty.from_dict(r) for r in resp]

    def get(self, dataset, concept):
        dataset_id = self._get_id(dataset)
        concept_id = self._get_id(concept)
        r = self._get(self._uri('/{dataset_id}/concepts/{id}', dataset_id=dataset_id, id=concept_id))
        r['dataset_id'] = r.get('dataset_id', dataset_id)
        r['schema'] = self.get_properties(dataset, concept)
        return Concept.from_dict(r, api=self.session)

    def delete(self, dataset, concept):
        dataset_id = self._get_id(dataset)
        concept_id = self._get_id(concept)
        return self._del(self._uri('/{dataset_id}/concepts/{id}', dataset_id=dataset_id, id=concept.id))

    def update(self, dataset, concept):
        assert isinstance(concept, Concept), "concept must be type Concept"
        data = concept.as_dict()
        data['id'] = concept.id
        dataset_id = self._get_id(dataset)
        r = self._put(self._uri('/{dataset_id}/concepts/{id}', dataset_id=dataset_id, id=concept.id), json=data)
        r['dataset_id'] = r.get('dataset_id', dataset_id)
        if concept.schema:
            r['schema'] = self.update_properties(dataset, concept)
        return Concept.from_dict(r, api=self.session)

    def create(self, dataset, concept):
        assert isinstance(concept, Concept), "concept must be type Concept"
        dataset_id = self._get_id(dataset)
        r = self._post(self._uri('/{dataset_id}/concepts', dataset_id=dataset_id), json=concept.as_dict())
        concept.id = r['id']
        r['dataset_id'] = r.get('dataset_id', dataset_id)
        if concept.schema:
            r['schema'] = self.update_properties(dataset, concept)
        return Concept.from_dict(r, api=self.session)

    def get_all(self, dataset):
        dataset_id = self._get_id(dataset)
        resp = self._get(self._uri('/{dataset_id}/concepts', dataset_id=dataset_id), stream=True)
        for r in resp:
            r['dataset_id'] = r.get('dataset_id', dataset_id)
            r['schema']     = self.get_properties(dataset, r['id'])
        concepts = [Concept.from_dict(r, api=self.session) for r in resp]
        return { c.type: c for c in concepts }

    def delete_instances(self, dataset, concept, *instances):
        dataset_id = self._get_id(dataset)
        concept_id = self._get_id(concept)
        ids = [self._get_id(instance) for instance in instances]

        return self._del(self._uri('/{dataset_id}/concepts/{id}/instances', dataset_id=dataset_id, id=concept_id), json=ids)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Concept Instances
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ConceptInstancesAPI(ConceptsAPIBase):
    base_uri = "/datasets"
    name = 'concepts.instances'

    def __init__(self, session):
        self.host = session._concepts_host
        super(ConceptInstancesAPI, self).__init__(session)

    def get(self, dataset, instance, concept=None):
        dataset_id = self._get_id(dataset)
        instance_id = self._get_id(instance)
        concept_type = self._get_concept_type(concept, instance)

        r = self._get(self._uri('/{dataset_id}/concepts/{concept_type}/instances/{id}', dataset_id=dataset_id, concept_type=concept_type, id=instance_id))
        r['dataset_id'] = r.get('dataset_id', dataset_id)
        return ConceptInstance.from_dict(r, api=self.session)

    def relations(self, dataset, instance, related_concept, concept=None):
        dataset_id = self._get_id(dataset)
        instance_id = self._get_id(instance)
        related_concept_type = self._get_id(related_concept)
        concept_type = self._get_concept_type(concept, instance)

        res = self._get(self._uri('/{dataset_id}/concepts/{concept_type}/instances/{id}/relations/{related_concept_type}', dataset_id=dataset_id, concept_type=concept_type, id=instance_id, related_concept_type=related_concept_type))

        relations = []
        for r in res:
            relationship = r[0]
            concept = r[1]

            relationship['dataset_id'] = relationship.get('dataset_id', dataset_id)
            concept['dataset_id'] = concept.get('dataset_id', dataset_id)

            relationship = RelationshipInstance.from_dict(relationship, api=self.session)
            concept = ConceptInstance.from_dict(concept, api=self.session)

            relations.append((relationship, concept))

        return relations

    def get_all(self, dataset, concept, limit=100):
        dataset_id = self._get_id(dataset)
        concept_type = self._get_concept_type(concept)

        resp = self._get(self._uri('/{dataset_id}/concepts/{concept_type}/instances', dataset_id=dataset_id, concept_type=concept_type), params=dict(limit=limit), stream=True)
        for r in resp:
          r['dataset_id'] = r.get('dataset_id', dataset_id)
        instances = [ConceptInstance.from_dict(r, api=self.session) for r in resp]

        return ConceptInstanceSet(concept, instances)

    def delete(self, dataset, instance):
        assert isinstance(instance, ConceptInstance), "instance must be type ConceptInstance"
        dataset_id = self._get_id(dataset)
        r = self._del(self._uri('/{dataset_id}/concepts/{concept_type}/instances/{id}', dataset_id=dataset_id, concept_type=instance.type, id=instance.id))
        r['dataset_id'] = r.get('dataset_id', dataset_id)
        return r

    def create(self, dataset, instance):
        assert isinstance(instance, ConceptInstance), "instance must be type ConceptInstance"
        dataset_id = self._get_id(dataset)
        r = self._post(self._uri('/{dataset_id}/concepts/{concept_type}/instances', dataset_id=dataset_id, concept_type=instance.type), json=instance.as_dict())
        r['dataset_id'] = r.get('dataset_id', dataset_id)
        return ConceptInstance.from_dict(r, api=self.session)

    def update(self, dataset, instance):
        assert isinstance(instance, ConceptInstance), "instance must be type ConceptInstance"
        dataset_id = self._get_id(dataset)
        r = self._put(self._uri('/{dataset_id}/concepts/{concept_type}/instances/{id}', dataset_id=dataset_id, concept_type=instance.type, id=instance.id), json=instance.as_dict())
        r['dataset_id'] = r.get('dataset_id', dataset_id)
        return ConceptInstance.from_dict(r, api=self.session)

    def create_many(self, dataset, concept, *instances):
        instance_type = instances[0].type
        for inst in instances:
            assert isinstance(inst, ConceptInstance), "instance must be type ConceptInstance"
            assert inst.type == instance_type, "Expected instance of type {}, found instance of type {}".format(instance_type, inst.type)
        dataset_id = self._get_id(dataset)
        values = [inst.as_dict() for inst in instances]
        resp = self._post(self._uri('/{dataset_id}/concepts/{concept_type}/instances/batch', dataset_id=dataset_id, concept_type=instance_type), json=values)
        for r in resp:
            r['dataset_id'] = r.get('dataset_id', dataset_id)
        instances = [ConceptInstance.from_dict(r, api=self.session) for r in resp]
        return ConceptInstanceSet(concept, instances)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Relationships
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ConceptRelationshipsAPI(ConceptsAPIBase):
    base_uri = "/datasets"
    name = 'concepts.relationships'

    def __init__(self, session):
        self.host = session._concepts_host
        self.instances = ConceptRelationshipInstancesAPI(session)
        super(ConceptRelationshipsAPI, self).__init__(session)

    def create(self, dataset, relationship):
        assert isinstance(relationship, Relationship), "Must be of type Relationship"
        dataset_id = self._get_id(dataset)
        r = self._post(self._uri('/{dataset_id}/relationships', dataset_id=dataset_id), json=relationship.as_dict())
        r['dataset_id'] = r.get('dataset_id', dataset_id)
        return Relationship.from_dict(r, api=self.session)

    def get(self, dataset, relationship):
        dataset_id = self._get_id(dataset)
        relationship_id = self._get_id(relationship)
        r = self._get(self._uri('/{dataset_id}/relationships/{r_id}', dataset_id=dataset_id, r_id=relationship_id))
        r['dataset_id'] = r.get('dataset_id', dataset_id)
        return Relationship.from_dict(r, api=self.session)

    def get_all(self, dataset):
        dataset_id = self._get_id(dataset)
        resp = self._get(self._uri('/{dataset_id}/relationships', dataset_id=dataset_id), stream=True)
        for r in resp:
          r['dataset_id'] = r.get('dataset_id', dataset_id)
        relations = [Relationship.from_dict(r, api=self.session) for r in resp]
        return {r.type: r for r in relations}

class ConceptRelationshipInstancesAPI(ConceptsAPIBase):
    base_uri = "/datasets"
    name = 'concepts.relationships.instances'

    def __init__(self, session):
        self.host = session._concepts_host
        super(ConceptRelationshipInstancesAPI, self).__init__(session)

    def get_all(self, dataset, relationship):
        dataset_id = self._get_id(dataset)
        relationship_id = self._get_id(relationship)

        resp = self._get(self._uri('/{dataset_id}/relationships/{r_id}/instances', dataset_id=dataset_id, r_id=relationship_id), stream=True)
        for r in resp:
          r['dataset_id'] = r.get('dataset_id', dataset_id)
        instances = [RelationshipInstance.from_dict(r, api=self.session) for r in resp]
        return RelationshipInstanceSet(relationship, instances)

    def get(self, dataset, instance, relationship=None):
        dataset_id = self._get_id(dataset)
        instance_id = self._get_id(instance)
        relationship_type = self._get_relationship_type(relationship, instance)
        r = self._get( self._uri('/{dataset_id}/relationships/{r_type}/instances/{id}', dataset_id=dataset_id, r_type=relationship_type, id=instance_id))
        r['dataset_id'] = r.get('dataset_id', dataset_id)
        return RelationshipInstance.from_dict(r, api=self.session)

    def delete(self, dataset, instance):
        assert isinstance(instance, RelationshipInstance), "instance must be of type RelationshipInstance"
        dataset_id = self._get_id(dataset)
        return self._del( self._uri('/{dataset_id}/relationships/{r_type}/instances/{id}', dataset_id=dataset_id, r_type=instance.type, id=instance.id))

    def link(self, dataset, relationship, source, destination, values=dict()):
        assert isinstance(source, (ConceptInstance, DataPackage)), "source must be an object of type ConceptInstance or DataPackage"
        assert isinstance(destination, (ConceptInstance, DataPackage)), "destination must be an object of type ConceptInstance or DataPackage"

        if isinstance(source, DataPackage):
            assert isinstance(destination, ConceptInstance), "DataPackages can only be linked to ConceptInstances"
            return self.session.concepts.proxies.create(dataset, source.id, relationship, destination, values, "ToTarget", "package")
        elif isinstance(destination, DataPackage):
            assert isinstance(source, ConceptInstance), "DataPackages can only be linked to ConceptInstances"
            return self.session.concepts.proxies.create(dataset, destination.id, relationship, source, values, "FromTarget", "package")
        else:
            dataset_id = self._get_id(dataset)
            relationship_type = self._get_relationship_type(relationship)
            values = [dict(name=k, value=v) for k,v in values.items()]
            instance = RelationshipInstance(dataset_id=dataset_id, type=relationship_type, source=source, destination=destination, values=values)
            return self.create(dataset, instance)

    def create(self, dataset, instance):
        assert isinstance(instance, RelationshipInstance), "instance must be of type RelationshipInstance"
        dataset_id = self._get_id(dataset)
        resp = self._post( self._uri('/{dataset_id}/relationships/{r_type}/instances', dataset_id=dataset_id, r_type=instance.type), json=instance.as_dict())
        r = resp[0] # responds with list
        r['dataset_id'] = r.get('dataset_id', dataset_id)
        return RelationshipInstance.from_dict(r, api=self.session)

    def create_many(self, dataset, *instances):
        assert all([isinstance(i, RelationshipInstance) for i in instances]), "instances must be of type RelationshipInstance"
        dataset_id = self._get_id(dataset)
        resp = self._post( self._uri('/{dataset_id}/relationships/{r_type}/instances', dataset_id=dataset_id, r_type=instance.type), json=instance.as_dict())
        for r in resp:
            r['dataset_id'] = r.get('dataset_id', dataset_id)
        return RelationshipInstance.from_dict(r, api=self.session)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Concept Proxies
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ConceptProxiesAPI(ConceptsAPIBase):
    base_uri = "/datasets"
    name = 'concepts.proxies'

    proxy_types = ["package"]
    direction_types = ["FromTarget", "ToTarget"]

    def __init__(self, session):
        self.host = session._concepts_host
        super(ConceptProxiesAPI, self).__init__(session)

    def get_all(self, dataset, proxy_type):
        dataset_id = self._get_id(dataset)
        r = self._get(self._uri('/{dataset_id}/proxy/{p_type}/instances', dataset_id=dataset_id, p_type=proxy_type))
        r['dataset_id'] = r.get('dataset_id', dataset_id)
        return r

    def get(self, dataset, proxy_type, proxy_id):
        dataset_id = self._get_id(dataset)
        r = self._get(self._uri('/{dataset_id}/proxy/{p_type}/instances/{p_id}', dataset_id=dataset_id, p_type=proxy_type, p_id=proxy_id))
        r['dataset_id'] = r.get('dataset_id', dataset_id)
        return r

    def create(self, dataset, external_id, relationship, concept_instance, values, direction = "ToConcept", proxy_type = "package", concept = None):
        assert proxy_type in self.proxy_types, "proxy_type must be one of {}".format(self.proxy_types)
        assert direction in self.direction_types, "direction must be one of {}".format(self.direction_types)

        dataset_id = self._get_id(dataset)
        concept_instance_id = self._get_id(concept_instance)
        concept_type = self._get_concept_type(concept, concept_instance)
        relationship_type = self._get_relationship_type(relationship)
        relationshipData = [dict(name=k, value=v) for k,v in values.items()]

        request = {}
        request['direction'] = direction
        request['externalId'] = external_id
        request['conceptType'] = concept_type
        request['conceptInstanceId'] = concept_instance_id
        request['relationshipType'] = relationship_type
        request['relationshipData'] = relationshipData

        r = self._post(self._uri('/{dataset_id}/proxy/{p_type}/instances', dataset_id=dataset_id, p_type=proxy_type), json=request)
        instance = r['relationshipInstance']
        instance['dataset_id'] = instance.get('dataset_id', dataset_id)
        return RelationshipInstance.from_dict(instance, api=self.session)
