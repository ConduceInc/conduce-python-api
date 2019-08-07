#!groovy

properties([buildDiscarder(logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '', daysToKeepStr: '14', numToKeepStr: '10')), [$class: 'ScannerJobProperty', doNotScan: false], [$class: 'RebuildSettings', autoRebuild: false, rebuildDisabled: false], pipelineTriggers([])])


node('debian') {
  try {
    stage("Plan") {
      checkout scm
      sh "git submodule update --init --remote"

      // Print environment variables
      environment = sh(script: 'env', returnStdout: true)
      print "${environment}"
      // Gather build info to pass to the pipeline
      build_info = [
          develop_commit_id: sh(script: "git rev-parse --short origin/develop| tr -d '\n'", returnStdout: true),
          master_commit_id : sh(script: "git rev-parse --short origin/master | tr -d '\n'", returnStdout: true),
          commit_id        : sh(script: "git rev-parse --short HEAD | tr -d '\n'", returnStdout: true),
          version          : sh(script: "cat doc/base.json | grep version | cut -d'\"' -f4", returnStdout: true)
      ]

      // Determine which pipeline to run based on which branch is building
      if (env.BRANCH_NAME.contains("PR-")) {
        version_suffix = "pr-${env.CHANGE_ID}"
        suffix = "pr"
      } else if (env.BRANCH_NAME == 'develop') {
        version_suffix = "develop+build-${env.BUILD_NUMBER}"
        suffix = "develop"
      } else if (env.BRANCH_NAME.contains('release')) {
        version_suffix = "${build_info['version']}+rc-${env.BUILD_NUMBER}"
        suffix = "to_test"
      } else if (env.BRANCH_NAME == 'master') {
        version_suffix = "${build_info['version']}"
        suffix = "master"
      }
      build_info['version_suffix'] = version_suffix
      echo "Version: ${build_info['version']}"
      echo "Installer Suffix: ${version_suffix}"
      echo "Loading Pipeline: ${suffix}"
      pipeline = load "tools/jenkins/pipeline_${suffix}.groovy"
    }
    // Set build status before we start
    currentBuild.result = "SUCCESS"

    pipeline.begin(build_info)
  }
  catch (org.jenkinsci.plugins.workflow.steps.FlowInterruptedException e) {
    // Cancel detected
    print e
    currentBuild.result = "ABORTED"
    throw e
  }
  catch (hudson.AbortException e) {
    // Abort detected
    print e
    if (e.getMessage().contains('script returned exit code 143')) {
      currentBuild.result = "ABORTED"
      throw e
    } else {
      currentBuild.result = "FAILURE"

      if(!env.BRANCH_NAME.contains("PR-")) {
        slackSend color: "danger", channel: "#jenkins", message: "Build Failure: <${env.JOB_URL}|${env.JOB_NAME}> <${env.BUILD_URL}|#${env.BUILD_NUMBER}> <${env.CHANGE_URL ?: 'https://github.com/ConduceInc/everything'}|(GitHub)>"
	slackSend color: "danger", channel: "#eng", message: "Build Failure: <${env.JOB_URL}|${env.JOB_NAME}> <${env.BUILD_URL}|#${env.BUILD_NUMBER}> <${env.CHANGE_URL ?: 'https://github.com/ConduceInc/everything'}|(GitHub)>"
      }
    }
  }
  catch (e) {
    // Error detected
    print e
    if (e.getMessage().contains('No changes')) {
      currentBuild.result = "ABORTED"
      throw e
    }
    currentBuild.result = "FAILURE"

    // Tell everyone we failed
    if(!env.BRANCH_NAME.contains("PR-")) {
      slackSend color: "danger", channel: "#jenkins", message: "Build Failure: <${env.JOB_URL}|${env.JOB_NAME}> <${env.BUILD_URL}|#${env.BUILD_NUMBER}> <${env.CHANGE_URL ?: 'https://github.com/ConduceInc/everything'}|(GitHub)>"
      slackSend color: "danger", channel: "#eng", message: "Build Failure: <${env.JOB_URL}|${env.JOB_NAME}> <${env.BUILD_URL}|#${env.BUILD_NUMBER}> <${env.CHANGE_URL ?: 'https://github.com/ConduceInc/everything'}|(GitHub)>"
    }
  }
  finally {
    deleteDir()
  }
}
