package com.chrima.transaction.event;

import com.chrima.events.api.EventType;
import com.chrima.events.api.model.IEventPayload;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
@EventType(value = TransactionCompletedEvent.EVENT_TYPE, topic = "transaction-events")
public class TransactionCompletedEvent implements IEventPayload {

  public static final String EVENT_TYPE = "transaction.completed";

  UUID transactionId;
  UUID productId;
  UUID priceId;
  String platformUserId;
  double amount;
}
