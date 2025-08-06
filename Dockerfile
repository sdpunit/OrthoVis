FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TOTALSEG_LICENSE="aca_ZE9G7WMK44CMT9"

WORKDIR /app

# System libraries for VTK and PySide6
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libegl1 \
    libgl1-mesa-glx \
    libxrender1 \
    libxext6 \
    libsm6 \
    libxcb1 \
    libfontconfig1 \
    libfreetype6 \
    libxi6 \
    libxrandr2 \
    libxinerama1 \
    libxkbcommon-x11-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# Setup TotalSegmentator
RUN totalseg_set_license -l "$TOTALSEG_LICENSE" \
 && totalseg_download_weights -t total \
 && totalseg_download_weights -t appendicular_bones

# # (Optional) Create a non-root user
# RUN adduser --disabled-password --gecos "" --uid 10001 appuser
# USER appuser

# Copy your app code
COPY . .

EXPOSE 8000

CMD ["python3", "classes/main.py"]