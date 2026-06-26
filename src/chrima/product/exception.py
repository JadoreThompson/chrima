from uuid import UUID


class ProductNotFoundException(Exception):
    def __init__(self, product_id: UUID):
        super().__init__("Product not found")
        self.product_id = product_id
