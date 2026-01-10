"""Oracle attachment registry (shadow-only attachments)."""

from abraxas.attachments.aalmanac_v1 import AALmanacConfig, build_aalmanac_attachment

ATTACHMENT_BUILDERS = {
    "aalmanac_v1": {
        "lane": "shadow",
        "builder": build_aalmanac_attachment,
        "config": AALmanacConfig(),
        "attach_path": "oracle.attachments.aalmanac_v1",
    }
}
