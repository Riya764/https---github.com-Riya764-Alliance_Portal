'''
for permissions for the all apps
'''
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    '''
    Custom permission to only allow owners of an object to edit it.
    '''
    @classmethod
    def has_object_permission(cls, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the user of the object.
        try:
            return obj.user_id == request.user.id
        except StandardError:
            return obj.id == request.user.id
