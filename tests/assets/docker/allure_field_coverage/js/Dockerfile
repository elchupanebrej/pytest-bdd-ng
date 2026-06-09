FROM node:20-slim

WORKDIR /app

# Create package.json
RUN cat > package.json << 'EOF'
{
  "name": "cucumber-field-coverage",
  "version": "1.0.0",
  "dependencies": {
    "@cucumber/cucumber": "^10.3.0"
  }
}
EOF

# Install dependencies
RUN npm install

# Create feature file with all schema-relevant scenarios
RUN mkdir -p features
RUN cat > features/field_coverage.feature << 'EOF'
@allure-fields
Feature: Schema Field Coverage
  Scenario: Passing scenario with steps and attachments
    Given a step with a parameter "browser" value "chromium"
    When I execute a step that produces an attachment
    Then the step passes with status "passed"
    And the result contains labels and links

  Scenario: Failing scenario with status details
    Given a step that fails
    When the step finishes with error message "assertion failed"
    Then the result contains statusDetails with message and trace
EOF

# Create step definitions
RUN mkdir -p features/support
RUN cat > features/support/steps.js << 'JS'
const { Given, When, Then } = require('@cucumber/cucumber');

Given('a step with a parameter {string} value {string}', function(name, value) {
  this.attach(JSON.stringify({ [name]: value }), 'application/json');
});

When('I execute a step that produces an attachment', function() {
  this.attach('Sample attachment content', 'text/plain');
});

Then('the step passes with status {string}', function(status) {
  if (status !== 'passed') {
    throw new Error(`Expected status ${status}`);
  }
});

Then('the result contains labels and links', function() {
  // Verified via allure output
});

Given('a step that fails', function() {
  throw new Error('Intentional failure for testing');
});

When('the step finishes with error message {string}', function(message) {
  // Error message captured
});

Then('the result contains statusDetails with message and trace', function() {
  // Verified via allure output
});
JS

# Create world with hooks
RUN cat > features/support/world.js << 'JS'
const { World, setWorldConstructor } = require('@cucumber/cucumber');

class AllureWorld extends World {
  constructor(props) {
    super(props);
    this.results = [];
  }
}

setWorldConstructor(AllureWorld);
JS

# Create cucumber.js config
RUN cat > cucumber.js << 'EOF'
module.exports = {
  default: {
    paths: ['features/**/*.feature'],
    require: ['features/support/**/*.js'],
    format: ['json:allure-results/cucumber.json'],
    formatOptions: { snippetInterface: 'async-await' }
  }
};
EOF

# Run cucumber
CMD ["npx", "cucumber-js", "--tags", "@allure-fields"]
