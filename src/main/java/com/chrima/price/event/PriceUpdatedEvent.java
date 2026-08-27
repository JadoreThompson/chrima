package com.chrima.price.event;

import com.chrima.events.api.EventType;
import com.chrima.events.api.model.IEventPayload;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
@EventType(value = PriceUpdatedEvent.EVENT_TYPE, topic = "price-events")
public class PriceUpdatedEvent implements IEventPayload {

  public static final String EVENT_TYPE = "price.updated";

  UUID priceId;
  double amount;
}
