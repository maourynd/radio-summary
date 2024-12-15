# Use an official Python runtime as a parent image
FROM python:3.9

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Specify Chrome version and download matching ChromeDriver
ENV CHROME_VERSION 114.0.5735.90
RUN wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/${CHROME_VERSION}/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver

# Verify installations
RUN google-chrome --version
RUN chromedriver --version

# Set the working directory in the container
WORKDIR /app

# Set environment variables for Chrome
ENV GOOGLE_CHROME_SHIM=/usr/bin/google-chrome
ENV PATH=$PATH:/usr/local/bin

# Copy all project files into the container
COPY . /app

# Set PYTHONPATH to include the project root
ENV PYTHONPATH="/app"

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1

# Set environment variables for Selenium
ENV PATH="/usr/local/bin:${PATH}"

# Expose the application port (if needed, e.g., Flask default is 5000)
EXPOSE 5000

# Define the command to run your application
CMD ["python", "main/execute.py"]
