from rest_framework import serializers

from django.core.exceptions import ValidationError

# **********FUNCTIONS**********

def setObjectAttributes(obj,data,attributesToSet):
    for attribute in attributesToSet:
        try:
            setattr(obj,attribute,data[attribute])
        except KeyError:
            pass

def setDataAttributes(obj,data,attributesToSet):
    for attribute in attributesToSet:
        try:
            data[attribute] = getattr(obj,attribute)
        except KeyError:
            pass

def createOrUpdateObject(objIn,modelIn,data,attributesToSet,requiredAttributes):
    try:
        # Try to get existing object
        obj = modelIn.objects.get(pk=objIn.instance.id)
    except (modelIn.DoesNotExist, AttributeError):
        # If object does not exist create new object
        try:
            obj = modelIn(**{attribute: data[attribute] for attribute in requiredAttributes}) # initiate object with required attributes
        except KeyError:
            raise ValidationError('Key Error: A required field is missing')
    # Set attributes on object and return
    setObjectAttributes(obj,data,attributesToSet)
    return obj

def validateObject(objIn,modelIn,data,attributesToSet,requiredAttributes):
    # Get or create object and run full_clean
    obj = createOrUpdateObject(objIn,modelIn,data,attributesToSet,requiredAttributes)
    obj.full_clean()
    # Set data values from cleaned values on object
    setDataAttributes(obj,data,attributesToSet)
    return data

class CustomValidationSerializer(serializers.ModelSerializer):
    def validate(self, data):
        # Get required validation fields
        if hasattr(self, 'requiredValidationFields'):
            requiredValidationFields = self.requiredValidationFields
        else:
            requiredValidationFields = [f.name for f in self.Meta.model._meta.get_fields() if (f.concrete and not f.blank and f.editable)]

        # Get all validation fields
        if hasattr(self, 'allValidationFields'):
            allValidationFields = self.allValidationFields
        else:
            allValidationFields = [f.name for f in self.Meta.model._meta.get_fields() if (f.concrete and f.name in self.fields and f.name not in ['id', 'creationDateTime', 'updatedDateTime'])]

        print(requiredValidationFields)
        print(allValidationFields)

        # Run validation and return validated data
        validateObject(self, self.Meta.model, data, allValidationFields, requiredValidationFields)
        return data
