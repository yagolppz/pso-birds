import unittest

from objectives import OBJECTIVES, get_objective
from objectives.wifi_router import wifi_router, wifi_router_definition


class ObjectivesTests(unittest.TestCase):
    def test_wifi_router_is_registered(self) -> None:
        """Verifica que wifi_router está registrado en OBJECTIVES."""
        self.assertIn("wifi_router", OBJECTIVES)
        objective = get_objective("wifi_router")
        self.assertEqual(objective.name, "wifi_router")
        self.assertIn("router WiFi", objective.description)

    def test_wifi_router_accepts_3d_position_returns_float(self) -> None:
        """Verifica que wifi_router acepta posición 3D y devuelve float."""
        position = [0.0, 0.0, 2.5]  # Posición razonable
        result = wifi_router(position)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)

    def test_wifi_router_definition_has_correct_properties(self) -> None:
        """Verifica que la definición de wifi_router tiene propiedades correctas."""
        definition = wifi_router_definition()
        self.assertEqual(definition.name, "wifi_router")
        self.assertEqual(len(OBJECTIVES), 6)  # sphere, sleepy_sphere, rastrigin, ackley, rosenbrock, wifi_router
        self.assertEqual(definition.suggested_lower_bound, -10.0)
        self.assertEqual(definition.suggested_upper_bound, 10.0)

    def test_good_position_has_lower_cost_than_bad_position(self) -> None:
        """Verifica que una posición buena tiene menor coste que una mala."""
        # Posición buena: cerca del centro, altura razonable, sin obstáculos
        good_position = [0.0, 0.0, 2.5]
        good_cost = wifi_router(good_position)
        
        # Posición mala: lejos de dispositivos, altura baja (penalizada), cerca de obstáculo
        bad_position = [5.0, 5.0, 0.5]  # Lejos, altura baja, cerca de obstáculo
        bad_cost = wifi_router(bad_position)
        
        self.assertLess(good_cost, bad_cost)

    def test_wifi_router_is_deterministic(self) -> None:
        """Verifica que wifi_router es determinista."""
        position = [1.0, -1.0, 3.0]
        result1 = wifi_router(position)
        result2 = wifi_router(position)
        result3 = wifi_router(position)
        
        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3)

    def test_wifi_router_raises_error_for_wrong_dimensions(self) -> None:
        """Verifica que wifi_router rechaza posiciones con dimensión incorrecta."""
        with self.assertRaises(ValueError):
            wifi_router([1.0, 2.0])  # 2D en lugar de 3D
        
        with self.assertRaises(ValueError):
            wifi_router([1.0, 2.0, 3.0, 4.0])  # 4D en lugar de 3D

    def test_wifi_router_height_penalty(self) -> None:
        """Verifica penalización por altura no razonable."""
        # Altura buena
        good_height = wifi_router([0.0, 0.0, 2.5])
        # Altura demasiado baja
        low_height = wifi_router([0.0, 0.0, 1.0])
        # Altura demasiado alta
        high_height = wifi_router([0.0, 0.0, 5.0])
        
        self.assertLess(good_height, low_height)
        self.assertLess(good_height, high_height)


if __name__ == "__main__":
    unittest.main()