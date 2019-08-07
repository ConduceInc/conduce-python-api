def begin(build_info) {
  common = load 'tools/jenkins/common.groovy'

  common.prepare(build_info)
  common.test_and_build()

  /*
  stage("Tag release") {
    sh "git tag ${build_info['version_suffix']}"
    sh "git push --tags"
  }
  */

  /*
  //TODO: deploy
  stage("Deploy package") {
  }
  stage("Deploy docs") {
  }
  */

  slackSend color: "good", channel: "#jenkins", message: "Conduce Python API ${build_info['version']} has been published"
}

return this
