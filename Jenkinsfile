pipeline {
    agent any

    stages {
        stage('Container Orchestration') {
            steps {
                echo 'Starting DevSecOps Docker Triad...'
                sh 'docker compose up -d'
                sh 'sleep 15' // Give LocalStack time to become fully healthy
            }
        }
        stage('Deploy Infrastructure') {
            steps {
                echo 'Provisioning Terraform resources into LocalStack...'
                sh 'terraform init'
                sh 'terraform apply -auto-approve'
            }
        }
    }
    post {
        always {
            echo 'Cleaning up DevSecOps lab to prevent port conflicts...'
            sh 'docker compose down'
        }
    }
}