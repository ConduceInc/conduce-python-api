def prepare(build_info) {
  stage("Prepare"){
    if(!env.BRANCH_NAME.contains("PR-")) {
      slackSend channel: "#jenkins", message: "Build Started: <${env.JOB_URL}|${env.JOB_NAME}> <${env.BUILD_URL}|#${env.BUILD_NUMBER}> <${env.CHANGE_URL ?: 'https://github.com/ConduceInc/conduce-python-api'}|(GitHub)>"
    }

    sh "rm -rf venv"
    sh "rm -rf htmlcov"
    sh "rm -rf doc/build"
    sh "python -m venv venv"
    sh ". venv/bin/activate && pip install -r requirements-dev.txt"

    milestone()
  }
}


def test_and_build() {
  stage("Unit tests") {
    sh ". venv/bin/activate && python -m unittest discover -v test/"
    milestone()
  }
  stage("Build docs") {
    sh """. venv/bin/activate
        cd doc
        make html"""
    milestone()
  }
}

def coverage_report() {
  stage("Generate Coverage Report") {
      sh """. venv/bin/activate
          coverage run --source conduce -m unittest discover -v test/
          coverage report
          coverage html
        """
    milestone()
  }
}

return this;
