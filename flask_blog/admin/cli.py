from __future__ import annotations

from typing import TYPE_CHECKING

import click
from email_validator import EmailNotValidError, validate_email  # type: ignore[import]

from flask_blog.admin.models import AdminUser
from flask_blog.database.core import db

if TYPE_CHECKING:
    from typing import Optional


def get_admin_user_by_email_address(
    *, email_address: str, raise_exception: Optional[bool] = True
) -> Optional[AdminUser]:
    """
    Retrieves the admin user by the given email address.

    Depending on `raise_exception`, a ClickException will be raised or None will be returned if the
    admin user is not found.
    """

    admin_user = AdminUser.get_by_email_address(email_address=email_address)

    if admin_user is None and raise_exception is True:
        raise click.ClickException("No admin user with this email address exists.")

    return admin_user


@click.command()
@click.argument("email_address")
def activate_user(email_address: str) -> None:
    """
    Activate an admin user.
    """

    admin_user = get_admin_user_by_email_address(email_address=email_address)
    assert admin_user is not None

    if not admin_user.is_active:
        admin_user.active = True
        db.session.commit()

        click.echo(f"Activated admin user {email_address}.")

    else:
        click.echo(f"Admin user {email_address} is already activated.")


@click.command()
def create_user() -> None:
    """
    Create an admin user.
    """

    # Email address
    email_address = click.prompt("Enter an email address")

    try:
        validate_email(email_address)
    except EmailNotValidError as exception:
        raise click.ClickException("Provide a valid email address.") from exception

    admin_user = get_admin_user_by_email_address(email_address=email_address, raise_exception=False)
    if admin_user is not None:
        raise click.ClickException("User with this email address already exists.")

    # Password
    password = click.prompt("Enter a password", hide_input=True, confirmation_prompt=True)
    if len(password) < 8:
        raise click.ClickException("Provide a password with at least 8 characters.")

    # Create admin user
    new_admin_user = AdminUser(email_address=email_address)
    new_admin_user.set_password_hash(raw_password=password)
    new_admin_user.rotate_public_id()
    db.session.add(new_admin_user)
    db.session.commit()

    click.echo(f"Created admin user {email_address}.")


@click.command()
@click.argument("email_address")
def deactivate_user(email_address: str) -> None:
    """
    Deactivate an admin user.
    """

    admin_user = get_admin_user_by_email_address(email_address=email_address)
    assert admin_user is not None

    if admin_user.is_active:
        admin_user.active = False
        db.session.commit()

        click.echo(f"Deactivated admin user {email_address}.")

    else:
        click.echo(f"Admin user {email_address} is already deactivated.")


@click.command()
@click.argument("email_address")
def delete_user(email_address: str) -> None:
    """
    Delete an admin user.
    """

    admin_user = get_admin_user_by_email_address(email_address=email_address)
    assert admin_user is not None

    click.confirm(f"Are you sure you want to delete admin user {email_address}", abort=True)

    db.session.delete(admin_user)
    db.session.commit()

    click.echo(f"Deleted admin user {email_address}.")


@click.command()
@click.argument("email_address")
def reset_user_password(email_address: str) -> None:
    """
    Reset an admin user's password.

    Also rotates the public ID to invalidate current login sessions.
    """

    admin_user = get_admin_user_by_email_address(email_address=email_address)
    assert admin_user is not None

    password = click.prompt("Enter a password", hide_input=True, confirmation_prompt=True)
    if len(password) < 8:
        raise click.ClickException("Provide a password with at least 8 characters.")

    admin_user.set_password_hash(raw_password=password)
    admin_user.rotate_public_id()
    db.session.commit()

    click.echo(f"Reset password for admin user {email_address}.")
