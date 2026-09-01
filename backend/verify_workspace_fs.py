import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from core.errors import ValidationError
from core.settings import settings
from core.workspace_fs import WorkspaceFilesystem
from services.code_analysis_service import CodeAnalysisService
from services.git_service import GitService

base = Path(tempfile.mkdtemp(prefix='melo-workspace-'))
settings.BASE_DIR = base

service = CodeAnalysisService()
created = service.write_file('notes.py', "print('first')\n", confirm=True)
assert created['created'] is True
updated = service.write_file('notes.py', "print('second')\n", confirm=True)
assert updated['created'] is False
assert (base / 'notes.py').read_text(encoding='utf-8') == "print('second')\n"

try:
    service.write_file('../outside.py', 'x', confirm=True)
    raise AssertionError('escape path should have failed')
except ValidationError:
    pass

ws_root = base / 'workspaces'
ws_a = WorkspaceFilesystem('workspace-a', base_root=ws_root)
ws_b = WorkspaceFilesystem('workspace-b', base_root=ws_root)
ws_a.write_file('notes.py', "print('A')\n")
assert (ws_root / 'workspace-a' / 'notes.py').read_text(encoding='utf-8') == "print('A')\n"

try:
    ws_a.resolve_safe_path('../workspace-b/secret.txt')
    raise AssertionError('path traversal not blocked')
except ValueError:
    pass

try:
    ws_b.resolve_safe_path('../../etc/passwd')
    raise AssertionError('absolute traversal not blocked')
except ValueError:
    pass

with patch('services.git_service.subprocess.run', return_value=Mock(returncode=0, stdout='diff -- app.py\n', stderr='')) as run:
    response = GitService(base / 'workspace-sandbox').diff('app.py')
    assert response == {'path': 'app.py', 'diff': 'diff -- app.py\n'}
    assert run.call_args.args[0][-2:] == ['--', 'app.py']

try:
    GitService(base / 'workspace-sandbox').diff('../outside.py')
    raise AssertionError('git diff should reject escape path')
except ValidationError:
    pass

print('workspace sandbox checks passed')
