import strawberry
import uuid
import datetime
import typing
from .BaseGQLModel import IDType

# Definuje lazy typy pro modely User a Group pomocí Annotated a strawberry.lazy.
UserGQLModel = typing.Annotated["UserGQLModel", strawberry.lazy(".userGQLModel")]
GroupGQLModel = typing.Annotated["GroupGQLModel", strawberry.lazy(".groupGQLModel")]

# Resolver pro získání primárního klíče entity.
@strawberry.field(description="""Entity primary key""")
def resolve_id(self) -> IDType:
    return self.id

# Resolver pro získání jména entity.
@strawberry.field(description="""Name """)
def resolve_name(self) -> str:
    return self.name

# Resolver pro získání anglického jména entity.
@strawberry.field(description="""English name""")
def resolve_name_en(self) -> str:
    return self.name_en

# Resolver pro získání času poslední aktualizace entity.
@strawberry.field(description="""Time of last update""")
def resolve_lastchange(self) -> datetime.datetime:
    return self.lastchange

# Resolver pro získání času vytvoření entity.
@strawberry.field(description="""Time of entity introduction""")
def resolve_created(self) -> typing.Optional[datetime.datetime]:
    return self.lastchange

# Funkce pro asynchronní získání uživatele podle ID.
async def resolve_user(user_id):
    from .userGQLModel import UserGQLModel
    result = None if user_id is None else await UserGQLModel.resolve_reference(user_id)
    return result

# Resolver pro získání informací o tom, kdo vytvořil entitu.
@strawberry.field(description="""Who created entity""")
async def resolve_createdby(self) -> typing.Optional["UserGQLModel"]:
    return await resolve_user(self.created_by)

# Resolver pro získání informací o tom, kdo provedl poslední změnu entity.
@strawberry.field(description="""Who made last change""")
async def resolve_changedby(self) -> typing.Optional["UserGQLModel"]:
    return await resolve_user(self.changedby)

# @strawberry.field(description="""Who made last change""")
# async def resolve_rbacobject(self) -> typing.Optional[RBACObjectGQLModel]:
#     from ._RBACObjectGQLModel import RBACObjectGQLModel
#     result = None if self.rbacobject is None else await RBACObjectGQLModel.resolve_reference(self.rbacobject_id)
#     return result

resolve_result_id: IDType = strawberry.field(description="primary key of CU operation object")
resolve_result_msg: str = strawberry.field(description="""Should be `ok` if descired state has been reached, otherwise `fail`.
For update operation fail should be also stated when bad lastchange has been entered.""")

# Vytvoří resolver pro skalární atribut entity.
def createAttributeScalarResolver(
    scalarType: None = None, 
    foreignKeyName: str = None,
    description="Retrieves item by its id",
    permission_classes=()
    ):

    assert scalarType is not None
    assert foreignKeyName is not None

    @strawberry.field(description=description, permission_classes=permission_classes)
    async def foreignkeyScalar(
        self, info: strawberry.types.Info
    ) -> typing.Optional[scalarType]:
        # 👇 self must have an attribute, otherwise it is fail of definition
        assert hasattr(self, foreignKeyName)
        id = getattr(self, foreignKeyName, None)
        
        result = None if id is None else await scalarType.resolve_reference(info=info, id=id)
        return result
    return foreignkeyScalar

# Vytvoří resolver pro vektorový atribut entity.
def createAttributeVectorResolver(
    scalarType: None = None, 
    whereFilterType: None = None,
    foreignKeyName: str = None,
    loaderLambda = lambda info: None, 
    description="Retrieves items paged", 
    skip: int=0, 
    limit: int=10):

    assert scalarType is not None
    assert foreignKeyName is not None

    @strawberry.field(description=description)
    async def foreignkeyVector(
        self, info: strawberry.types.Info,
        skip: int = skip,
        limit: int = limit,
        where: typing.Optional[whereFilterType] = None
    ) -> typing.List[scalarType]:
        
        params = {foreignKeyName: self.id}
        loader = loaderLambda(info)
        assert loader is not None
        
        wf = None if where is None else strawberry.asdict(where)
        result = await loader.page(skip=skip, limit=limit, where=wf, extendedfilter=params)
        return result
    return foreignkeyVector

# Vytvoří kořenový resolver pro získání entity podle jejího ID.
def createRootResolver_by_id(scalarType: None, description="Retrieves item by its id"):
    assert scalarType is not None
    @strawberry.field(description=description)
    async def by_id(
        self, info: strawberry.types.Info, id: IDType
    ) -> typing.Optional[scalarType]:
        result = await scalarType.resolve_reference(info=info, id=id)
        return result
    return by_id

# Vytvoří kořenový resolver pro stránkované získání entit.
def createRootResolver_by_page(
    scalarType: None, 
    whereFilterType: None,
    loaderLambda = lambda info: None, 
    description="Retrieves items paged", 
    skip: int=0, 
    limit: int=10):

    assert scalarType is not None
    assert whereFilterType is not None
    
    @strawberry.field(description=description)
    async def paged(
        self, info: strawberry.types.Info, 
        skip: int=skip, limit: int=limit, where: typing.Optional[whereFilterType] = None
    ) -> typing.List[scalarType]:
        loader = loaderLambda(info)
        assert loader is not None
        wf = None if where is None else strawberry.asdict(where)
        result = await loader.page(skip=skip, limit=limit, where=wf)
        return result
    return paged
