# CodeReviewProject

## Description
CodeReviewProject is a tool designed to facilitate efficient and constructive code reviews. It helps developers collaborate, provide feedback, and improve code quality by streamlining the review process. With features like automated suggestions, inline commenting, and version control integration, CodeReviewProject enhances team productivity. It was designed to gamify the reviewing experience, by adding a leaderboard system.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Contributing](#contributing)

## Installation
To install and run CodeReviewProject using Docker, follow these steps:

1. **Clone the repository**
   ```sh
   git clone https://github.com/MLHirth/CodeReviewProject.git
   ```
2. **Navigate into the project directory**
   ```sh
   cd CodeReviewProject
   ```
3. **Build the Docker image**
   ```sh
   docker build -t codereviewproject .
   ```
4. **Run the application using Docker**
   ```sh
   docker run -d -p 8000:8000 codereviewproject
   ```
5. **Access the application**
   Open your browser and navigate to `http://localhost:8000`.

## Usage
Watch the following video to see how to use CodeReviewProject:

(VIDEO WILL BE ADDED SOON...)

![Usage Video](insert-video-url-here)

## Features
- Automated code suggestions
- Inline commenting on pull requests
- Version control system (Git) integration
- Customizable review templates
- Detailed analytics on code quality

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch (`feature`).
3. Make changes and commit (`git commit -m "message"`).
4. Push to your branch (`git push origin feature`).
5. Open a Pull Request.


