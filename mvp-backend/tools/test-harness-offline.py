#!/usr/bin/env python3
"""Run backend regressions against disposable state with vendor networking blocked.

Run with the backend virtualenv's Python. Remaining arguments go to pytest.
Use --shared to exercise all shared runtime switches; production flags are untouched.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--shared', action='store_true')
    options, pytest_args = parser.parse_known_args()
    backend = Path(__file__).resolve().parents[1]
    scratch = Path(tempfile.mkdtemp(prefix='mvp-harness-tests-'))
    (scratch / 'sitecustomize.py').write_text(
        'import socket\n'
        'def blocked(*args, **kwargs):\n'
        '    raise RuntimeError("Outbound network disabled in harness validation")\n'
        'socket.socket.connect = blocked\n'
        'socket.create_connection = blocked\n'
    )
    env = os.environ.copy()
    env.update({
        'PYTHONPATH': str(scratch) + os.pathsep + str(backend),
        'PYTHON_DOTENV_DISABLED': '1',
        'MVP_DUCKDB_PATH': str(scratch / 'runtime' / 'test.duckdb'),
        'MVP_CHECKPOINT_DB_PATH': str(scratch / 'runtime' / 'checkpoints.sqlite'),
        'OPENAI_API_KEY': 'offline-dummy-key', 'TAVILY_API_KEY': 'offline-dummy-key',
        'ANTHROPIC_API_KEY': '', 'ELEVENLABS_API_KEY': '',
        'POSTHOG_API_KEY': '', 'POSTHOG_PERSONAL_API_KEY': '',
        'SENTRY_DSN': '', 'OTEL_SDK_DISABLED': 'true',
        'LANGCHAIN_TRACING_V2': 'false', 'LANGSMITH_TRACING': 'false',
        'SLACK_WEBHOOK_URL': '', 'APNS_KEY_PATH': '',
    })
    for surface in ('CHAT', 'COS', 'PARENT_VOICE', 'ONBOARDING', 'KID_TEXT', 'KID_VOICE'):
        env['MVP_SHARED_RUNTIME_' + surface] = '1' if options.shared else '0'
    log_path = scratch / 'pytest.log'
    print(f'Disposable state and full log: {scratch}', flush=True)
    with log_path.open('w') as log:
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
             *(pytest_args or ['tests'])],
            cwd=backend, env=env, stdout=log, stderr=subprocess.STDOUT,
        )
    print(log_path.read_text()[-20000:])
    print(f'Full log: {log_path}')
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
