from rest_framework import mixins, viewsets


class ListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    pass


class ListRetrieveViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    pass
