from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import TagModel, StoreModel, ItemModel
from schemas import TagSchema, TagAndItemSchema

blp = Blueprint("Tags", "tags", description="Operations on tags")

@blp.route("/store/<int:store_id>/tag")
class TagsInStore(MethodView):
    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)

        return store.tags.all()

    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        # if TagModel.query.filter(TagModel.store_id == store_id).first():
        if TagModel.query.filter(TagModel.store_id == store_id, TagModel.name == tag_data["name"]).first():
            abort(400, message="A tag with that name already exists in that store.")

        tag = TagModel(**tag_data, store_id=store_id)

        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(
                500,
                message=str(e),
            )

        return tag

@blp.route("/store/<int:store_id>/tag/<int:tag_id>")
class LinkTagsToStore(MethodView):
    @blp.response(201, TagSchema)
    # appends a tag to item
    def post(self, store_id, tag_id):
        store = StoreModel.query.get_or_404(store_id)
        tag = TagModel.query.get_or_404(tag_id)
    
        store.tags.append(tag)

        try:
            db.session.add(store)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Unable to add tag")
        
        return tag

@blp.route("/item/<int:item_id>/tag/<int:tag_id>")
class LinkTagsToItem(MethodView):
    @blp.response(201, TagSchema)
    # appends a tag to item
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        if item.store.id != tag.store.id:
             abort(400, message="Make sure item and tag belong to the same store before linking.")
    
        item.tags.append(tag)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Unable to add tag")
        
        return tag
    
    @blp.response(200, TagAndItemSchema)
    # unlinks tag from item
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        item.tags.remove(tag)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Unable to add tag")
        
        return {"message": "Connection between item and tag has been remove", "item": item, "tag": tag}


@blp.route("/tag/<int:tag_id>")
class Tag(MethodView):
    @blp.response(200, TagSchema)
    def get(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        return tag
    
    @blp.response(
        202,
        description="Deletes a tag if no item is tagged with it.",
        example={"message": "Tag deleted."}
    )

    @blp.alt_response(404, description="Tag not found")

    @blp.alt_response(
        400, 
        description="Returned if tag is assigned to one or more items. In this case, the tag is not deleted"
        )

    #completely delete tag
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)

        if not tag.items:
            db.session.delete(tag)
            db.session.commit()
            return {"message": "Tag deleted successfully!"}
        abort(
            400,
            message="Could not delete this tag. Please make sure tag is not connected with any items, then attempt again."
        )
