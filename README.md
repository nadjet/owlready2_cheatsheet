# owlready2_cheatsheet

This is a set of functions that I have been using to process an owl graph. Given base name and folder path, it loads and parse a local rdf/xml file and prints some of its content (object properties, individuals, etc).

The code contains the following functions:

1. ```create_class_by_name``` Create a class given a name
2. ```get_classes``` Get all classes
3. ```has_object_properties``` Check if instance has object properties
4. ```is_domain_or_range``` Returns true if item is domain or range individual.
5. ```get_object_properties``` Get all the object properties of the ontology
6. ```get_data_properties``` Get all the data properties of the ontology
7. ```check_instance``` Find an instance by string name
8. ```get_instance_classes``` Get classes of an instance
9. ```get_class_by_name``` Get a class by its string name
10. ```attach_instance_to_class``` Attach an instance to a class
11. ```get_individuals``` Get all the individuals in the ontology
12. ```add_data_property``` Add one or more values as data properties of a specific type to an instance
13. ```get_uri``` Create a uri given the base name and class name
14. ```create_instance_of_class``` Create an instance of a class
15. ```remove_superclasses``` Remove the superclasses of a given class if they are superclasses of a given super class (if we'd want to attach the given class to the given superclass)
16. ```attach_class_to_subclass``` Given a class name and that class super class name, and a sub class, assign the super class of that subclass, creating it if necessary. There can be more than one super class to assign (csv string).
17. ```attach_class_to_superclass```Same as  ```attach_class_to_subclass`` but for subclass,
18. ```get_class``` Given a class name and its super class name, we create that new class if it does not exist or we return the existing one
19. ```add_object_property``` Given an instance (domain) and an object property, assign another instance by name as range of the domain instance object property. There can be more than one (comma separated).
20. ```is_instance_of_class``` Returns True if the instance is of the class name. If descendants input argument is set to True then it looks for the subclasses too.
