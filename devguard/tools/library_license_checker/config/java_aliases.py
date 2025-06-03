JAVA_IMPORT_ALIASES = {
    # JSON & Serialization
    "com.google.gson": ("com.google.code.gson", "gson"),
    "com.fasterxml.jackson": ("com.fasterxml.jackson.core", "jackson-databind"),
    "org.json": ("org.json", "json"),

    # Apache Commons
    "org.apache.commons.lang3": ("org.apache.commons", "commons-lang3"),
    "org.apache.commons": ("org.apache.commons", "commons-lang3"),
    "org.slf4j.impl": ("org.slf4j", "slf4j-simple"),
    "org.apache.logging.log4j.core": ("org.apache.logging.log4j", "log4j-core"),
    "org.apache.commons.io": ("org.apache.commons", "commons-io"),
    "org.apache.commons.codec": ("commons-codec", "commons-codec"),
    "org.apache.commons.collections4": ("org.apache.commons", "commons-collections4"),

    # Logging
    "org.slf4j": ("org.slf4j", "slf4j-api"),
    "ch.qos.logback": ("ch.qos.logback", "logback-classic"),
    "org.apache.logging.log4j": ("org.apache.logging.log4j", "log4j-core"),

    # Testing
    "org.junit": ("junit", "junit"),
    "org.junit.jupiter": ("org.junit.jupiter", "junit-jupiter-api"),
    "org.mockito": ("org.mockito", "mockito-core"),

    # Spring Framework
    "org.springframework": ("org.springframework", "spring-context"),
    "org.springframework.boot": ("org.springframework.boot", "spring-boot-starter"),
    "org.springframework.web": ("org.springframework", "spring-web"),

    # Database & ORM
    "org.hibernate": ("org.hibernate", "hibernate-core"),
    "javax.persistence": ("javax.persistence", "javax.persistence-api"),
    "com.zaxxer.hikari": ("com.zaxxer", "HikariCP"),

    # Web & HTTP Clients
    "org.apache.http": ("org.apache.httpcomponents", "httpclient"),
    "okhttp3": ("com.squareup.okhttp3", "okhttp"),
    "retrofit2": ("com.squareup.retrofit2", "retrofit"),

    # Google Libraries
    "com.google.common": ("com.google.guava", "guava"),
    "com.google.api.client": ("com.google.api-client", "google-api-client"),

    # AWS SDK
    "com.amazonaws.services.s3": ("com.amazonaws", "aws-java-sdk-s3"),
    "com.amazonaws.auth": ("com.amazonaws", "aws-java-sdk-core"),

    # XML & Data Formats
    "javax.xml.parsers": ("javax.xml", "javax.xml.parsers"),
    "javax.xml.bind": ("javax.xml.bind", "jaxb-api"),

    # Kotlin Interop
    "kotlin.jvm": ("org.jetbrains.kotlin", "kotlin-stdlib"),

    # JSON Schema / Validation
    "com.networknt.schema": ("com.networknt", "json-schema-validator"),

    # Misc
    "javax.servlet": ("javax.servlet", "javax.servlet-api"),
    "jakarta.servlet": ("jakarta.servlet", "jakarta.servlet-api"),
    "org.flywaydb.core": ("org.flywaydb", "flyway-core"),

    # Add more below based on use cases you see
}

KNOWN_GOOD_JAVA_VERSIONS = {
    "com.fasterxml.jackson.core:jackson-databind": "2.15.0",
    "com.google.code.gson:gson": "2.10.1",
    "org.slf4j:slf4j-api": "1.7.36",
    "org.junit.jupiter:junit-jupiter-api": "5.9.3",
    "com.squareup.okhttp3:okhttp": "4.12.0",
    "org.apache.commons:commons-lang3": "3.12.0",
    # Extend as needed
}

TRUSTED_LICENSES = {
    "org.slf4j:slf4j-api": "MIT",
    "org.apache.commons:commons-lang3": "Apache-2.0"
}