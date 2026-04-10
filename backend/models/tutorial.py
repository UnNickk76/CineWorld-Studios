# CineWorld Studio's - Tutorial Models

from datetime import datetime, timezone


def tutorial_status_template():
    return {
        "static": {
            "version": 0,
            "last_update": None,
            "content": []
        },
        "velion": {
            "version": 0,
            "last_update": None,
            "steps": []
        },
        "guest": {
            "version": 0,
            "last_update": None,
            "steps": []
        },
        "frozen_sections": {
            "release_notes": {
                "enabled": False,
                "label": "In aggiornamento"
            },
            "system_notes": {
                "enabled": False,
                "label": "In aggiornamento"
            }
        },
        "update_job": {
            "status": "idle",
            "progress": 0,
            "current_step": "",
            "type": "",
            "started_at": None
        }
    }
