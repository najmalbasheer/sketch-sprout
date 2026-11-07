plugins {
    id("com.android.application")
}

android {
    namespace = "com.sketchsprout.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.sketchsprout.app"
        minSdk = 24
        targetSdk = 35
        versionCode = (System.getenv("GITHUB_RUN_NUMBER") ?: "1").toInt()
        versionName = "1.0." + (System.getenv("GITHUB_RUN_NUMBER") ?: "0")
    }

    signingConfigs {
        // A fixed key kept in the repo, so each new build installs over the last one.
        create("family") {
            storeFile = file("sketchsprout.keystore")
            storePassword = "sketchsprout"
            keyAlias = "sketchsprout"
            keyPassword = "sketchsprout"
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("family")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation("androidx.core:core:1.13.1")
}
