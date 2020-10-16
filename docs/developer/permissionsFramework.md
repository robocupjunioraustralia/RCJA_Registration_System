# Permissions Framework

The coordination app builds on the builting Django permissions to provides a powerful framework for providing limited admin access to users based on role and state. A use can be given permissions by either:
- Granting them superuser status - this is a very powerful role that should be only given to a small number of system administrators.
- Creating a Coordinator object for the user, which can be assigned a state (or no state for permissions across all states) as well as a permissions level. Assigning a Coordinator Full permissions is preferred to giving them superuser status, as it provides all of the same business permissions but without some potentially destructive admin actions.

The setting of Django permissions is handled by the Coordinator app and is disabled in the frontend.

## Permissions for global objects

To add State based permissions on a model it is necessary to define `coordinatorPermissions` on the Model.


## Simple State based permissions

The minimum required to add state based permissions to a model is to define:
- `coordinatorPermissions` on the model
- `getState` on the model
- Inherit from `AdminPermissions` for the ModelAdmin
- Define `stateFilterLookup` on the ModelAdmin

To filter foreign keys that link to that model, you must define `fieldsToFilterRequest` on the ModelAdmin for the Model with the field.