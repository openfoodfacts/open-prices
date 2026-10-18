# History

Open Prices keeps the history of `Price`, `Proof` and `Location` objects, using [django-simple-history](https://django-simple-history.readthedocs.io/).

## What is tracked 🕰️

Each change (creation, update, deletion) stores a snapshot of the object, along with:

- the date of the change
- the type of change: `+` (created), `~` (changed) or `-` (deleted)
- the user who made the change (if authenticated)

## API

- `GET /api/v1/prices/{id}/history` & `GET /api/v1/proofs/{id}/history`: list the changes of an object

`Location` history is only available in the Django admin for now.

## Cleanup

A record is created on every save, even when no field changed. A daily task removes these duplicate entries.

See also [Moderation](moderation.md): moderators can check an object's history before editing or deleting it.
