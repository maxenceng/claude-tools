/**
 * Shared kernel. Open module: its nested packages stay visible to other contexts.
 * Keep this small — anything that belongs to one context belongs in that context.
 */
@ApplicationModule(type = OPEN)
package com.example.app.shared;

import static org.springframework.modulith.ApplicationModule.Type.OPEN;

import org.springframework.modulith.ApplicationModule;
