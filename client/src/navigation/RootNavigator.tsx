import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../theme/colors';
import WorkoutScreen from '../screens/WorkoutScreen';
import RoutinesScreen from '../screens/RoutinesScreen';
import CatalogScreen from '../screens/CatalogScreen';
import CoachScreen from '../screens/CoachScreen';

export type RootTabParamList = {
  Workout: undefined;
  Routines: undefined;
  Catalog: undefined;
  Coach: undefined;
};

const Tab = createBottomTabNavigator<RootTabParamList>();

type IoniconName = keyof typeof Ionicons.glyphMap;

export default function RootNavigator() {
  return (
    <Tab.Navigator
      initialRouteName="Workout"
      screenOptions={({ route }) => ({
        headerStyle: {
          backgroundColor: Colors.surface,
          shadowColor: 'transparent',
          elevation: 0,
          borderBottomWidth: 1,
          borderBottomColor: Colors.surfaceBorder,
        },
        headerTitleStyle: {
          color: Colors.textPrimary,
          fontWeight: '700',
          fontSize: 18,
        },
        headerTintColor: Colors.textPrimary,
        tabBarStyle: {
          backgroundColor: Colors.surface,
          borderTopWidth: 1,
          borderTopColor: Colors.surfaceBorder,
          height: 64,
          paddingBottom: 10,
          paddingTop: 8,
        },
        tabBarActiveTintColor: Colors.accent,
        tabBarInactiveTintColor: Colors.textMuted,
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
        },
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: IoniconName = 'barbell-outline';

          if (route.name === 'Workout') {
            iconName = focused ? 'barbell' : 'barbell-outline';
          } else if (route.name === 'Routines') {
            iconName = focused ? 'clipboard' : 'clipboard-outline';
          } else if (route.name === 'Catalog') {
            iconName = focused ? 'book' : 'book-outline';
          } else if (route.name === 'Coach') {
            iconName = focused ? 'chatbubble-ellipses' : 'chatbubble-ellipses-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Workout" component={WorkoutScreen} options={{ title: 'Workout' }} />
      <Tab.Screen name="Routines" component={RoutinesScreen} options={{ title: 'Routines' }} />
      <Tab.Screen name="Catalog" component={CatalogScreen} options={{ title: 'Catalog' }} />
      <Tab.Screen name="Coach" component={CoachScreen} options={{ title: 'AI Coach' }} />
    </Tab.Navigator>
  );
}
