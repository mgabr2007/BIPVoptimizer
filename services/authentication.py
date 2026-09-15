"""OIDC identity and PostgreSQL ownership context; no application passwords."""
import hashlib
import json
import time
from dataclasses import dataclass
import streamlit as st


@dataclass(frozen=True)
class Principal:
    issuer: str
    subject: str
    display_name: str = ''

    @property
    def key(self):
        return hashlib.sha256(json.dumps([self.issuer, self.subject], separators=(',', ':')).encode()).hexdigest()


def current_principal():
    if not st.user.is_logged_in:
        raise PermissionError('Sign in to access projects')
    issuer, subject = st.user.get('iss'), st.user.get('sub')
    if not issuer or not subject:
        raise PermissionError('The identity provider must supply issuer and subject claims')
    if st.user.get('exp') is not None and float(st.user['exp']) <= time.time():
        raise PermissionError('Your sign-in has expired. Sign out and sign in again.')
    return Principal(str(issuer), str(subject), str(st.user.get('name', 'Researcher')))


def require_login():
    if not st.user.is_logged_in:
        st.title('BIPV research workspace')
        st.write('Sign in to access your projects and saved analysis runs.')
        try:
            configured = 'auth' in st.secrets
        except FileNotFoundError:
            configured = False
        if configured:
            st.button('Sign in', on_click=st.login, type='primary')
        else:
            st.info('Sign-in is not configured for this deployment. Contact the workspace administrator.')
        st.stop()
    try:
        principal = current_principal()
    except PermissionError as exc:
        st.error(str(exc))
        st.button('Sign out', on_click=st.logout)
        st.stop()
    if st.session_state.get('_identity_key') != principal.key:
        st.session_state.clear()
        st.session_state['_identity_key'] = principal.key
    st.sidebar.caption(f'Signed in as {principal.display_name}')
    if st.sidebar.button('Sign out'):
        st.session_state.clear()
        st.logout()
        st.stop()
    return principal


def bind_connection(conn, principal=None):
    """Bind every connection, including legacy raw SQL, to a verified identity.

    Fail closed for privileged roles, missing migrations and suspended accounts.
    Session settings survive the legacy code's intermediate commits; connections
    are not shared between identities. Async pooled connections reset on release.
    """
    principal = principal or current_principal()
    with conn.cursor() as cur:
        cur.execute('SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user')
        if any(cur.fetchone()):
            raise PermissionError('Use a database runtime role without SUPERUSER or BYPASSRLS')
        cur.execute("SELECT version FROM app_migrations WHERE version = '002_multiuser'")
        if cur.fetchone() is None:
            raise PermissionError('The multi-user database migration is required')
        cur.execute("SELECT set_config('app.identity_key', %s, false)", (principal.key,))
        cur.execute('''INSERT INTO app_users(identity_key, display_name) VALUES (%s, %s)
                       ON CONFLICT(identity_key) DO UPDATE SET display_name=EXCLUDED.display_name
                       RETURNING id, disabled''', (principal.key, principal.display_name))
        user_id, disabled = cur.fetchone()
        if disabled:
            raise PermissionError('This workspace account is disabled')
        cur.execute("SELECT set_config('app.user_id', %s, false)", (str(user_id),))
    conn.commit()
    return user_id


async def bind_async_connection(conn, principal=None):
    principal = principal or current_principal()
    role = await conn.fetchrow('SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname=current_user')
    if role['rolsuper'] or role['rolbypassrls']:
        raise PermissionError('Privileged database roles are not allowed for application access')
    if not await conn.fetchval("SELECT version FROM app_migrations WHERE version='002_multiuser'"):
        raise PermissionError('The multi-user database migration is required')
    await conn.execute("SELECT set_config('app.identity_key', $1, false)", principal.key)
    row = await conn.fetchrow('''INSERT INTO app_users(identity_key,display_name) VALUES($1,$2)
                             ON CONFLICT(identity_key) DO UPDATE SET display_name=EXCLUDED.display_name
                             RETURNING id,disabled''', principal.key, principal.display_name)
    if row['disabled']:
        raise PermissionError('This workspace account is disabled')
    await conn.execute("SELECT set_config('app.user_id', $1, false)", str(row['id']))
