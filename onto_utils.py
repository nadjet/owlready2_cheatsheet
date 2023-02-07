import owlready2
from general_utils import deaccent, parse_string_csv
import logging
from logging_utils import init_logging
import types
import os
import sys

init_logging(write_to_log_file=False)


class OntoUtils:

    def __init__(self, folder_path, base_iri='http://www.co-ode.org/ontologies/pizza/pizza.owl#'):
        # the folder path has to contain the file (pizza.owl) that uses base iri
        logging.info(f'Opening ontology with base iri "{base_iri}" in folder "{folder_path}"...')
        try:
            if not os.path.isdir(folder_path) or not os.path.exists(folder_path):
                logging.error(f'"{folder_path}" does not exist or is not a folder')
            owlready2.onto_path.append(folder_path)
            self.onto = owlready2.get_ontology(base_iri).load()
            self.onto.base_iri = base_iri
        except owlready2.base.OwlReadyOntologyParsingError:
            logging.error(f'Cannot load ontology file with base iri "{base_iri}" under folder "{dir_name}"')
            raise owlready2.base.OwlReadyOntologyParsingError

    def create_class_by_name(self,class_name: str):
        class_name = class_name.strip()
        class_name = deaccent(class_name)
        cls = self.get_class_by_name(class_name)
        return cls()

    def get_classes(self):
        classes = {}
        for cls in self.onto.classes():
            classes[cls.name] = cls
        return classes

    def has_object_properties(self,item):
        if self.is_class(item._name):
            return False
        for prop in item.get_properties():
            if isinstance(prop, owlready2.ObjectPropertyClass):
                return True
        return False

    def is_domain_or_range(self, item):
        if self.is_class(item._name):
            return False
        for instance in self.onto.individuals():
            if instance.name == item._name:
                return True
            props = instance.get_properties()
            for prop in props:
                if prop[instance] == item._name:
                    return True
        return False

    def get_object_properties(self):
        props = {}
        for prop in self.onto.object_properties():
            props[prop.name] = prop
        return props

    def get_data_properties(self):
        props = {}
        for prop in self.onto.data_properties():
            props[prop.name] = prop
        return props

    def check_instance(self, instance_name: str):
        instance = self.onto.search_one(iri=self.onto.base_iri + instance_name)
        if (instance is None or instance == "") and instance_name in self.get_classes():
            logging.error(f"Uri {instance_name} is a class, not an instance. Please check.")
            return None
        return instance

    @staticmethod
    def get_instance_classes(instance):
        return instance.is_a

    def get_class_by_name(self, class_name: str):
        classes_dict = self.get_classes()
        if class_name in classes_dict:
            return classes_dict[class_name]
        return None

    def attach_instance_to_class(self, instance, class_name: str):
        cls = self.get_class_by_name(class_name)
        if instance is not None and cls not in instance.is_a:
            if instance!=cls:
                instance.is_a.append(cls)
            else:
                raise ValueError(f"Instance '{instance}' and class '{cls}' are the same")
        return instance

    def get_individuals(self) -> {}:
        individuals = {}
        try:
            for instance in self.onto.individuals():
                if instance.name in individuals:
                    logging.error(f"Individual occurring twice: {instance.name}")
                individuals[instance.name] = instance
        except ValueError:
            raise
        return {x.name: x for x in self.onto.individuals()}

    def add_data_property(self, property, property_value, instance, is_multiple:bool):
        if property.name in self.get_data_properties() and len(property.range)>0 and property.range[0] == str:
            if is_multiple:
                for item in parse_string_csv(property_value):
                    property[instance].append(item)
            else:
                property[instance].append(property_value)
        else:
            raise(f"Error creating data property '{property.name}' with value '{property_value}' for instance '{instance}'")

    @staticmethod
    def get_uri(base_name: str, class_name: str):
        base_name = base_name.strip()
        class_name = class_name.strip()
        base_name = base_name.replace(" ", "_")
        class_name = class_name.replace(" ", "_")
        return deaccent("__".join([base_name, class_name]))

    def create_instance_of_class(self, instance_name: str, class_name: str):
        instance_name = OntoUtils.get_uri(instance_name, class_name)
        individuals = self.get_individuals()
        if instance_name in individuals:
            logging.info(f"instance with name {instance_name} already exists")
            return individuals[instance_name]
        cls = self.get_class_by_name(class_name)
        # instance is already a class
        instance_class = self.get_class_by_name(instance_name)
        if instance_class is not None:
            return instance_class
        return cls(instance_name)

    def remove_superclasses(self, subclass, super_class):
        subclass_superclasses = subclass.is_a
        if subclass != super_class:
            # we remove the superclasses of subclass if they already are superclasses of super_class
            superclass_superclasses = super_class.is_a
            for subclass_superclass in subclass_superclasses:
                if subclass_superclass in superclass_superclasses and subclass_superclass!=super_class:
                    subclass.is_a.remove(subclass_superclass)

    def attach_class_to_subclass(self, sub_cls, super_class_name, super_class_class, is_multiple: bool):
        if not is_multiple:
            superclass = self.get_class(super_class_name, super_class_class)
            if sub_cls!=superclass  and superclass not in sub_cls.is_a: # we don't allow loops
                sub_cls.is_a.append(superclass)
        else:
            names = parse_string_csv(super_class_name)
            for name in names:
                superclass = self.get_class(name, super_class_class)
                if sub_cls!= superclass and superclass not in sub_cls.is_a:
                    sub_cls.is_a.append(superclass)

    def attach_class_to_superclass(self, super_cls, sub_class_name, sub_class_class, is_multiple: bool):
        if not is_multiple:
            subclass = self.get_class(sub_class_name, sub_class_class)
            if subclass!=super_cls:
                subclass.is_a.append(super_cls)
        else:
            names = parse_string_csv(sub_class_name)
            for name in names:
                subclass = self.get_class(name, sub_class_class)
                if subclass!=super_cls:
                    subclass.is_a.append(super_cls)

    def get_class(self, class_name, super_class_name):
        uri = OntoUtils.get_uri(class_name, super_class_name)
        cls = self.get_class_by_name(uri)
        if cls is None:
            super_cls = self.get_class_by_name(super_class_name)
            if super_cls is not None:
                if super_cls!=cls:
                    cls = types.new_class(uri, (super_cls,))
                else:
                    raise(f"Found cycle {cls}, {super_cls}")
                return cls
        else:
            return cls

    def add_object_property(self, property, instance_range_name, instance_domain, is_multiple: bool):
        try :
            if property.name in self.get_object_properties() and property.range[0].name in self.get_classes():
                if not is_multiple:
                    instance_range = self.create_instance_of_class(instance_range_name, property.range[0].name)
                    property[instance_domain].append(instance_range)
                else:
                    for item in parse_string_csv(instance_range_name):
                        instance_range = self.create_instance_of_class(item, property.range[0].name)
                        property[instance_domain].append(instance_range)
            else:
                logging.error(f"Error creating object property {property.name} with domain  {instance_domain} and range value '{instance_range_name}'")
        except ValueError:
            raise

    def is_instance_of_class(self, instance, class_name, descendants=True):
        if instance.__class__.name != class_name and not descendants:
            return False
        elif instance.__class__.name == class_name:
            return True
        elif descendants:
            cls = self.get_class_by_name(class_name)
            for descendant in cls.descendants():
                if class_name==descendant.name:
                    return True
        return False


if __name__ == '__main__':
    dir_name = sys.argv[1] # folder where owl file is
    logging.info('Processing data...')
    onto_utils = OntoUtils(dir_name)
    individuals = onto_utils.get_individuals()
    data_properties_dict = onto_utils.get_data_properties()
    object_properties_dict = onto_utils.get_object_properties()
    classes = onto_utils.get_classes()
    print('Classes=', classes)
    print('Data properties=', data_properties_dict)
    print('Object properties=', object_properties_dict)
    print('Individuals=', individuals)
    instance = onto_utils.check_instance('Italy')
    print(f'Instance for "Italy" is {instance}')
    classes = OntoUtils.get_instance_classes(instance)
    print(f'Classes for "Italy" are {classes}')
    logging.info('Done!')

