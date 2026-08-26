package com.chrima;

import org.junit.jupiter.api.Test;
import org.springframework.modulith.core.ApplicationModules;

class SpringModulithTest {

    private final ApplicationModules modules = ApplicationModules.of(ChrimaApplication.class);

    @Test
    void verifyPackageConformity() {
        modules.verify();
    }
}
