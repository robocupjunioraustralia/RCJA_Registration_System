# Permissions Framework

The coordination app builds on the builting Django permissions to provides a powerful framework for providing limited admin access to users based on role and state. A use can be given permissions by either:
- Granting them superuser status - this is a very powerful role that should be only given to a small number of system administrators.
- Creating a Coordinator object for the user, which can be assigned a state (or no state for permissions across all states) as well as a permissions level. Assigning a Coordinator Full permissions is preferred to giving them superuser status, as it provides all of the same business permissions but without some potentially destructive admin actions.

The setting of Django permissions is handled by the Coordinator app and is disabled in the frontend.

## Permissions for global objects

To add State based permissions on a model it is necessary to define `stateCoordinatorPermissions` on the Model.


## Simple State based permissions

The minimum required to add state based permissions to a model is to define:
- `stateCoordinatorPermissions` on the model
- `getState` on the model
- Inherit from `AdminPermissions` for the ModelAdmin
- Define `stateFilterLookup` on the ModelAdmin

To filter foreign keys that link to that model, you must define `fieldsToFilterRequest` on the ModelAdmin for the Model with the field.


## Definitions

### `stateCoordinatorPermissions`
Defined on the model class.
Must be defined if admin inherits from `AdminPermissions`.
Defines the permissions for a state level coordinator

### `globalCoordinatorPermissions`
Defined on the model class.
Defines the permissiosn that apply to coordinators of all states (a coordinator where state=None). If not defined global coordinators will inherit permissions from `stateCoordinatorPermissions`.

### `getState`
Defined on the model class.

### `stateFilterLookup`
Defined on the admin class.
String using double underscore notation to the coordinator for the model via the state field.

### `globalFilterLookup`
Defined on the admin class.
None if no state based filtering for the model and should return the entire unfiltered queryset if the user has the required permissions.
String using double underscore notation to the state for the model if state filtering, in which case the objects with no state will be returned.
Leave undefined to not return global objects to state coordinators - will still be returned for global coordinators and super users.
