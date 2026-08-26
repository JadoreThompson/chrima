package com.chrima.events.api;

import com.chrima.events.api.model.IEventPayload;
import java.io.IOException;

public interface IEventService {

  void publish(String eventType, IEventPayload payload, String idempotencyKey) throws IOException;
}
