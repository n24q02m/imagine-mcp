import sys
import os

path = 'src/imagine_mcp/dispatcher.py'
with open(path, 'r') as f:
    lines = f.readlines()

new_lines = []
skip = 0
for i, line in enumerate(lines):
    if skip > 0:
        skip -= 1
        continue

    if '_DNS_RESOLVER_POOL = concurrent.futures.ThreadPoolExecutor(' in line:
        new_lines.append('_DNS_RESOLVER_POOL = concurrent.futures.ThreadPoolExecutor(\n')
        new_lines.append('    max_workers=16, thread_name_prefix="dns_resolver"\n')
        new_lines.append(')\n')
        new_lines.append('\n')
        new_lines.append('# Pool for parallelizing high-level dispatch tasks like validation and media detection\n')
        new_lines.append('_DISPATCH_POOL = concurrent.futures.ThreadPoolExecutor(\n')
        new_lines.append('    max_workers=16, thread_name_prefix="dispatch_worker"\n')
        new_lines.append(')\n')
        # Skip the original definition
        if 'max_workers=20' in lines[i+1]:
             skip = 2
        else:
             skip = 2 # assuming it was max_workers=4 before my sed
    elif 'def dispatch_understand(' in line:
        # Find the end of the docstring and the validation loop
        j = i
        while 'has_video = "video" in media_types' not in lines[j]:
            j += 1

        new_lines.extend(lines[i:i+10]) # Docstring and start
        # Wait, let's just replace the whole function body or specific parts
        # Safer to find specific markers

        # We want to replace from 'if provider is None:' to 'has_video = "video" in media_types'
        pass

    new_lines.append(line)

# Let's just use a more direct approach since I can read the whole file
with open(path, 'r') as f:
    content = f.read()

old_pool = """_DNS_RESOLVER_POOL = concurrent.futures.ThreadPoolExecutor(
    max_workers=20, thread_name_prefix="dns_resolver"
)"""

new_pool = """_DNS_RESOLVER_POOL = concurrent.futures.ThreadPoolExecutor(
    max_workers=16, thread_name_prefix="dns_resolver"
)

# Pool for parallelizing high-level dispatch tasks like validation and media detection
_DISPATCH_POOL = concurrent.futures.ThreadPoolExecutor(
    max_workers=16, thread_name_prefix="dispatch_worker"
)"""

content = content.replace(old_pool, new_pool)

old_dispatch = """    if provider is None:
        provider = _default_provider()
    _validate(provider, tier)
    if not media_urls:
        raise InvalidMediaTypeError("media_urls is empty")
    for i, u in enumerate(media_urls):
        _validate_url(u, f"media_urls[{i}]")

    media_types = [detect_media_type(u) for u in media_urls]
    has_video = "video" in media_types"""

new_dispatch = """    if provider is None:
        provider = _default_provider()
    _validate(provider, tier)
    if not media_urls:
        raise InvalidMediaTypeError("media_urls is empty")

    def _validate_and_detect(indexed_url: tuple[int, str]) -> str:
        i, u = indexed_url
        _validate_url(u, f"media_urls[{i}]")
        return detect_media_type(u)

    # Parallelize DNS validation and media detection to avoid N+1 sequential blocking.
    # We use a separate pool (_DISPATCH_POOL) to avoid deadlocks with _DNS_RESOLVER_POOL
    # which is used internally by _validate_url.
    media_types = list(_DISPATCH_POOL.map(_validate_and_detect, enumerate(media_urls)))
    has_video = "video" in media_types"""

content = content.replace(old_dispatch, new_dispatch)

with open(path, 'w') as f:
    f.write(content)
