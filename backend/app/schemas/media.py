from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field


class MediaRead(BaseModel):
    id: str
    destination_id: Optional[str] = None
    journal_entry_id: Optional[str] = None
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    caption: Optional[str] = None
    upload_date: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def url(self) -> str:
        """Compute the URL from the file path."""
        # file_path is like /app/media/{dest_id}/{filename}
        # We need to return /media/{dest_id}/{filename}
        if "/media/" in self.file_path:
            return "/media/" + self.file_path.split("/media/", 1)[1]
        return f"/media/{self.destination_id}/{self.file_name}"

    @computed_field
    @property
    def thumbnail_url(self) -> Optional[str]:
        """Compute the thumbnail URL."""
        if self.file_type and self.file_type.startswith("image/"):
            if "/media/" in self.file_path:
                parts = self.file_path.split("/media/", 1)[1]
                dir_part = parts.rsplit("/", 1)[0] if "/" in parts else ""
                return f"/media/{dir_part}/thumb_{self.file_name}"
            return f"/media/{self.destination_id}/thumb_{self.file_name}"
        return self.url
