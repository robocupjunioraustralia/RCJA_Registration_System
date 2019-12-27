from django.shortcuts import render, get_object_or_404,redirect

# Create your views here.
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import login, authenticate
from django.core.exceptions import ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from rest_framework import status, viewsets
from rest_framework.response import Response
from django.urls import reverse
from django.db.models.deletion import ProtectedError

# Create your views here.

#*******************Pages**********


# **********CUSTOM CLASSES****




# *****PERMISSIONS*****

class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_superuser
        )

class AuthenticatedReadOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.method in SAFE_METHODS
        )

class EditableOrReadOnly(BasePermission):
    def has_object_permission(self,request,view,obj):
        if request.method in SAFE_METHODS:
            return True
        try:
            return obj.editingAllowed()
        except AttributeError:
            return True

class AuthenticatedPutPatch(BasePermission):
    # Allow PUT or PATCH requests, use only if further permission checking at object level
    def has_permission(self,request,view):
        return request.user and request.user.is_authenticated and (request.method == 'PUT' or request.method == 'PATCH')

# *****VIEWSETS*****

class CustomModelViewSet(viewsets.ModelViewSet):
    # Default permissions
    permission_classes = (EditableOrReadOnly, IsAuthenticated, IsSuperUser)

    ordering_fields = [] # Set to pk, override on each model viewset, to ensure only desired fields are used

    # Override destroy to return an error if delete not allowed because of protected downstream objects
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({'status': 'success'},status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            return Response({'status': 'failed', 'detail':'Cannot delete because of protected objects'},status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({'status': 'failed', 'detail':e.messages},status=status.HTTP_403_FORBIDDEN)

    # Return correct serializer based on action
    def get_serializer_class(self):
        if not self.request.user.is_superuser and hasattr(self, 'student_action_serializers'):
            if self.action in self.student_action_serializers:
                return self.student_action_serializers[self.action]
        if hasattr(self, 'action_serializers'):
            if self.action in self.action_serializers:
                return self.action_serializers[self.action]
        return super(CustomModelViewSet, self).get_serializer_class()

class StudentReadCustomModelViewSet(CustomModelViewSet):
    permission_classes = (EditableOrReadOnly, IsAuthenticated, IsSuperUser | AuthenticatedReadOnly)

    # Filter queryset based on student permissions
    def get_queryset(self):
        # Set queryset order by
        orderBy = ['id']
        if hasattr(self, 'querysetOrderBy'):
            orderBy = self.querysetOrderBy

        # Select related
        querysetSelectRelated = []
        if hasattr(self, 'querysetSelectRelated'):
            querysetSelectRelated = self.querysetSelectRelated

        # Prefetch related
        querysetPrefetchRelated = []
        if hasattr(self, 'querysetPrefetchRelated'):
            querysetPrefetchRelated = self.querysetPrefetchRelated

        # Prepare common portions of qs
        qs = self.userFilterModel.objects.select_related(*querysetSelectRelated).prefetch_related(*querysetPrefetchRelated)
        if hasattr(self, 'querysetAnnotationMethods'):
            for method in self.querysetAnnotationMethods:
                qs = getattr(self.userFilterModel, method)(qs)

        # Return queryset
        if hasattr(self, 'userFilterModel'):
            user = self.request.user
            if user.is_superuser:
                return qs.order_by(*orderBy)
            if (hasattr(self, 'userFilterField') or hasattr(self, 'additionalFilterFields')):
                if hasattr(self, 'userFilterField') and hasattr(self, 'additionalFilterFields'):
                    filterDict = {**{self.userFilterField: user}, **self.additionalFilterFields}
                elif hasattr(self, 'userFilterField'):
                    filterDict = {self.userFilterField: user}
                elif hasattr(self, 'additionalFilterFields'):
                    filterDict = self.additionalFilterFields
                return qs.filter(**filterDict).order_by(*orderBy)
            return None
        return self.queryset
