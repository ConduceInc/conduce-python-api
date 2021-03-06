def begin(build_info) {
  common = load 'tools/jenkins/common.groovy'

  stage("Rebase"){
    //has_label_skip_rebase = sh(script: "python tools/get-github-pr-labels.py ${env.CHANGE_ID} | grep skip_rebase", returnStatus: true) == 0
    //if(!has_label_skip_rebase) {
      try {
        sh "git rebase origin/${env.CHANGE_TARGET}"
      } catch(e) {
        // A failed rebase leaves the repository in a bad states for the next build;
        // Abort the rebase so the git repo is clean for the next build.
        sh "git rebase --abort"
        throw e
      }
    //}
    milestone()
  }

  common.prepare(build_info)
  common.test_and_build()

  try {
    common.coverage_report()
  }
  catch (e) {
    print e
    throw e
  }
  finally {
    stage("Archive artifacts"){
      archive "htmlcov/**"
      milestone()
    }

    stage("Cleanup"){
      sh "rm -rf venv"
      sh "rm -rf htmlcov"
      sh "rm -rf doc/build"
    }
  }
}

return this
