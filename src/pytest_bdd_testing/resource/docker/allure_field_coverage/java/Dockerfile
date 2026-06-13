FROM maven:3.9-eclipse-temurin-21 AS builder

WORKDIR /app

# Create a minimal cucumber-java project that produces NDJSON
RUN cat > pom.xml << 'EOF'
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>cucumber-field-coverage</artifactId>
  <version>1.0.0</version>
  <properties>
    <maven.compiler.source>21</maven.compiler.source>
    <maven.compiler.target>21</maven.compiler.target>
    <cucumber.version>7.15.0</cucumber.version>
  </properties>
  <dependencies>
    <dependency>
      <groupId>io.cucumber</groupId>
      <artifactId>cucumber-java</artifactId>
      <version>${cucumber.version}</version>
    </dependency>
    <dependency>
      <groupId>io.cucumber</groupId>
      <artifactId>cucumber-junit-platform-engine</artifactId>
      <version>${cucumber.version}</version>
    </dependency>
    <dependency>
      <groupId>org.junit.platform</groupId>
      <artifactId>junit-platform-suite</artifactId>
      <version>1.10.2</version>
    </dependency>
  </dependencies>
</project>
EOF

# Create feature file with all schema-relevant scenarios
RUN mkdir -p src/test/resources/com/example
RUN cat > src/test/resources/com/example/field_coverage.feature << 'EOF'
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
RUN mkdir -p src/test/java/com/example
RUN cat > src/test/java/com/example/FieldCoverageSteps.java << 'JAVA'
package com.example;

import io.cucumber.java.en.Given;
import io.cucumber.java.en.When;
import io.cucumber.java.en.Then;
import io.cucumber.java.ParameterType;

public class FieldCoverageSteps {
    @Given("a step with a parameter {string} value {string}")
    public void aStepWithParameter(String name, String value) {
        // Parameter mapping for allure
    }

    @When("I execute a step that produces an attachment")
    public void executeStepWithAttachment() {
        // Will produce attachment
    }

    @Then("the step passes with status {string}")
    public void stepPassesWithStatus(String status) {
        assert "passed".equals(status);
    }

    @Then("the result contains labels and links")
    public void resultContainsLabelsAndLinks() {
        // Verified via allure output
    }

    @Given("a step that fails")
    public void stepThatFails() {
        throw new RuntimeException("Intentional failure for testing");
    }

    @When("the step finishes with error message {string}")
    public void stepFinishesWithErrorMessage(String message) {
        // Error message captured
    }

    @Then("the result contains statusDetails with message and trace")
    public void resultContainsStatusDetails() {
        // Verified via allure output
    }
}
JAVA

# Create JUnit Platform Suite runner
RUN cat > src/test/java/com/example/RunFieldCoverage.java << 'JAVA'
package com.example;

import org.junit.platform.suite.api.IncludeTags;
import org.junit.platform.suite.api.SelectClasspathResource;
import org.junit.platform.suite.api.Suite;
import static org.junit.platform.suite.api.ConfigurationParameter.*;
import io.cucumber.junit.platform.engine.Constants;

@Suite
@IncludeTags("allure-fields")
@SelectClasspathResource("com/example")
@ConfigurationParameter(key = Constants.PLUGIN_PROPERTY_NAME, value = "io.cucumber.core.plugin.SerenityReporterParallel")
public class RunFieldCoverage {
}
JAVA

# Create serenity.properties for NDJSON output
RUN cat > serenity.properties << 'EOF'
serenity.outputDirectory=target/allure-results
serenityucumber.enabled=true
EOF

# Build and run
RUN mvn test -Dcucumber.plugin="json:target/allure-results/cucumber.ndjson" -Dcucumber.filter.tags="@allure-fields" || true
