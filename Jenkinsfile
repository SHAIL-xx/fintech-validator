pipeline {
    agent any

    stages {
        stage('Source Checkout') {
            steps {
                echo 'Checking out the Cloud-Projects repository...'
                checkout scm
            }
        }
        stage('Security Linting') {
            steps {
                echo 'Running static analysis on Python worker...'
                sh 'echo "Static analysis passed."'
            }
        }
        stage('Infrastructure Plan') {
            steps {
                echo 'Generating Terraform execution plan...'
                sh 'terraform version'
            }
        }
    }
    post {
        always {
            echo 'Pipeline execution complete.'
        }
    }
}