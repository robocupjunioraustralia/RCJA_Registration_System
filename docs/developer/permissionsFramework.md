# Permissions Framework

The coordination app builds on the built-in Django permissions to provide a powerful framework for providing limited admin access to users based on role and state. A user can be given permissions by either:
- Granting them superuser status - this is a very powerful role that should be only given to a small number of system administrators.
- Creating a Coordinator object for the user, which can be assigned a state (or no state for permissions across all states) as well as a permissions level. Assigning a Coordinator Full permissions is preferred to giving them superuser status, as it provides all of the same business permissions but without some potentially destructive admin powers.

A coordinator can be either a global coordinator (state = None) or a state level coordinator. A global coordinator can manage all states as well as perform some global actions, such as editing some global objects.

The setting of Django permissions is handled by the Coordinator app and is disabled in the frontend.

## Simple state based permissions

The minimum required to implement state based permissions on a model is to:
- define `stateCoordinatorPermissions` on the model
- define `getState` on the model
- Inherit from `AdminPermissions` for the admin
- Define `stateFilterLookup` on the admin

To filter foreign key fields that link to the model, you must include the foreign key field in `fkFilterFields` on the ModelAdmin for the model with the field.

## Global objects

To add State based permissions on a model it is necessary to define `stateCoordinatorPermissions` on the model. If the admin inherits from `AdminPermissions` you must also define `stateCoordinatorViewGlobal = True` on the model. Inheriting from `AdminPermissions` is optional where the model is only global, but it is recommended to inherit from `AdminPermissions` so that future changes are enforced.

By default superusers can edit global objects and global coordinator permissions are defined by `stateCoordinatorPermissions`. To provide global coordinators with additional permissions or if `stateCoordinatorPermissions` you must define `globalCoordinatorPermissions`.

There are three possible scenarios for global objects:
- Only superusers have access. Don't define `stateCoordinatorPermissions`, `getState` or any other permissions method. Don't inherit from `AdminPermissions`. Superuser only access is the default. For example `InvoiceSettings`.
- Model has no connection to state. Don't define `getState`, don't define `globalFilterLookup` or `stateFilterLookup` (is impossible to do so anyway). For state coordinators to view must define `stateCoordinatorPermissions` and if want global coordinators to be able to edit (in addition to superusers) must define `globalCoordinatorPermissions`.
- Model has a connection to state, but the state field may be None, resulting in global objects. If you want state coordinators with the appropriate permissions to be able to view global objects (with permissions as defined in `stateCoordinatorPermissions`), must set `stateCoordinatorViewGlobal = True`. Must also define `getState`. Must also inherit from `AdminPermissions` on admin. Must define both `stateFilterLookup` and `globalFilterLookup`. If state coordinator should only be able to view objects with a state do not set `stateCoordinatorViewGlobal = True` and do not define `globalFilterLookup`, but must define `stateCoordinatorPermissions`, `getState` and `stateFilterLookup`. In both cases global coordinator permissions will be defined by `globalCoordinatorPermissions` if defined or `stateCoordinatorPermissions`.

## Definitions

| Name                        | Defined On      | Type           | Required                                       | Explanation                    |
| ------------- | ------------- | ------------- | ------------- | ------------- |
| `stateCoordinatorPermissions` | Model | Function returns list | Unless only superusers have access. Must be defined if admin inherits from `AdminPermissions`. | Takes permission level and returns the Django permissions. |
| `stateCoordinatorViewGlobal` | Model | Boolean | On global models if state coordinators can view global objects. |  |
| `globalCoordinatorPermissions` | Model | Function returns list | If global coordinators should have different permissions to state coordinators. | Takes permission level and returns the Django permissions, for global coordinators. Based on the coordinator status of the user, not whether the object that this is defined on is a global object. Can be defined on models that are never global to give global coordinators different permissions. |
| `getState` | Model | Function returns state object | If object is filtered through relationship with state. | Returns the state that this object is related to. |
| `stateFilterLookup` | Admin | String | If object is filtered through relationship with state. | Relationship of this model to state coordinator using double underscore notation. |
| `globalFilterLookup` | Admin | String | If object is filtered through relationship with state and state coordinators should have access to globals. | Relationship of this model to state using double underscore notation. |
| `fkFilterFields` | Admin | Dictionary | If model has foreign key fields that need to be filtered based on coordinator permissions. |  |
| `fkObjectFilterFields` | Admin  | Function returns dictionary | If model has foreign key fields that require custom filtering logic. |  |

### `AdminPermissions`
The class that provides advanced coordinator permissions for the model admin. Must inherit from this class or only builtin Django permissions will apply.

### `stateCoordinatorPermissions`
Defined on the model class. Must be defined if admin inherits from `AdminPermissions`.
Defines the permissions for a state level coordinator.

### `stateCoordinatorViewGlobal`
Defined on the model class.
If True state coordinators can view objects without a state or where the state is None.

### `globalCoordinatorPermissions`
Defined on the model class.
Defines the permissions that apply to global coordinators (a coordinator of all states, a coordinator where state=None). If not defined global coordinators will inherit permissions from `stateCoordinatorPermissions`.

### `getState`
Defined on the model class.
Should return the state of the object.

### `stateFilterLookup`
Defined on the admin class.
String using double underscore notation to the coordinator for the model via the state field.

### `globalFilterLookup`
Defined on the admin class.
String using double underscore notation to the state for the model if state filtering, in which case the objects with no state will be returned.

### `fkFilterFields`
Defined on the admin class.
A dictionary of dictionaries that defines foreign key fields that should have their queryset filtered using the coordinator permissions. Can also specify whether a field should be required for state and global coordinators.

### `fkObjectFilterFields`
Defined on the admin class.
Returns a dictionary of dictionaries that specifies the filtering of foreign key querysets based only on the current object and the request. Useful where custom field filtering logic is required. Must handle cases where obj=None.
