import ast
import io
import tarfile

import mkp

DIRECTORIES = [
    'agents', 'checkman', 'checks', 'doc', 'inventory', 'notifications',
    'pnp-templates', 'web',
]


def test_load_bytes(original_mkp_file):
    package = mkp.load_bytes(original_mkp_file)

    assert type(package) == mkp.Package
    assert package.info['title'] == 'Title of test'


def test_load_file(original_mkp_file, tmpdir):
    tmpdir.join('test.mkp').write_binary(original_mkp_file)

    package = mkp.load_file(str(tmpdir.join('test.mkp')))

    assert type(package) == mkp.Package
    assert package.info['title'] == 'Title of test'


def test_extract_files(original_mkp_file, tmpdir):
    package = mkp.load_bytes(original_mkp_file)

    package.extract_files(str(tmpdir))

    assert tmpdir.join('agents', 'special', 'agent_test').exists()
    assert tmpdir.join('checkman', 'test').exists()
    assert tmpdir.join('checkman', 'test').open().read() == 'title: Hello World!\n'


def test_pack_to_bytes(tmpdir):
    info = {
        'files': {'agents': ['special/agent_test']},
        'title': 'Test package',
    }
    tmpdir.join('agents', 'special', 'agent_test').write_binary(b'hello', ensure=True)

    data = mkp.pack_to_bytes(info, str(tmpdir))

    bytes_io = io.BytesIO(data)
    archive = tarfile.open(fileobj=bytes_io)

    info_file = archive.extractfile('info').read()
    extracted_info = ast.literal_eval(info_file.decode())
    assert extracted_info['files'] == info['files']
    assert extracted_info['title'] == info['title']
    assert extracted_info['version.packaged'] == 'python-mkp'

    agents_archive_file = archive.extractfile('agents.tar')
    agents_archive = tarfile.open(fileobj=agents_archive_file, mode='r:')
    agent_file = agents_archive.extractfile('special/agent_test')
    assert agent_file.read() == b'hello'


def test_pack_to_file(tmpdir):
    info = {
        'files': {'agents': ['special/agent_test']},
        'title': 'Test package',
    }
    tmpdir.join('agents', 'special', 'agent_test').write_binary(b'hello', ensure=True)

    outfile = tmpdir.join('test.mkp')

    mkp.pack_to_file(info, str(tmpdir), str(outfile))

    archive = tarfile.open(str(outfile))

    info_file = archive.extractfile('info').read()
    extracted_info = ast.literal_eval(info_file.decode())
    assert extracted_info['files'] == info['files']
    assert extracted_info['title'] == info['title']
    assert extracted_info['version.packaged'] == 'python-mkp'

    agents_archive_file = archive.extractfile('agents.tar')
    agents_archive = tarfile.open(fileobj=agents_archive_file, mode='r:')
    agent_file = agents_archive.extractfile('special/agent_test')
    assert agent_file.read() == b'hello'


def test_find_files_searches_all_directories(tmpdir):
    for directory in DIRECTORIES:
        tmpdir.join(directory, 'test').write_binary(b'Foo', ensure=True)

    result = mkp.find_files(str(tmpdir))
    for directory in DIRECTORIES:
        assert result[directory] == ['test']


def test_find_files_searches_subdirectories(tmpdir):
    tmpdir.join('agents', 'special', 'agent_test').write_binary(b'hello', ensure=True)

    result = mkp.find_files(str(tmpdir))

    assert result['agents'] == ['special/agent_test']


def test_find_files_ignores_hidden_files_and_dirs(tmpdir):
    tmpdir.join('agents', '.hidden').write_binary(b'hello', ensure=True)
    tmpdir.join('agents', 'test~').write_binary(b'hello', ensure=True)
    tmpdir.join('agents', '.hidden_dir', 'visible_file').write_binary(b'hello', ensure=True)

    result = mkp.find_files(str(tmpdir))

    assert result['agents'] == []


def test_pack_and_unpack_covers_all_known_directories(tmpdir):
    info = {
        'files': {key: ['test'] for key in DIRECTORIES},
    }
    source = tmpdir.join('source').mkdir()
    dest = tmpdir.join('dest').mkdir()

    for directory in DIRECTORIES:
        source.join(directory, 'test').write_binary(b'Foo', ensure=True)

    package_bytes = mkp.pack_to_bytes(info, str(source))
    package = mkp.load_bytes(package_bytes)
    package.extract_files(str(dest))

    for directory in DIRECTORIES:
        assert dest.join(directory, 'test').exists()
