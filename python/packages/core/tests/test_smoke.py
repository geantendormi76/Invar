def test_core_package_importable() -> None:
    import invar

    assert invar.__name__ == "invar"
