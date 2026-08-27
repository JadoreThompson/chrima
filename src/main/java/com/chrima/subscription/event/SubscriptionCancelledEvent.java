package com.chrima.subscription.event;

import com.chrima.events.api.EventType;
import com.chrima.events.api.model.IEventPayload;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
@EventType(value = SubscriptionCancelledEvent.EVENT_TYPE, topic = "subscription-events")
public class SubscriptionCancelledEvent implements IEventPayload {

  public static final String EVENT_TYPE = "subscription.cancelled";

  UUID subscriptionBalanceId;
  String externalId;
  String platformUserId;
  UUID productId;
}
