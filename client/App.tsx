// client/App.tsx
import React from 'react';
import { StatusBar } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import RootNavigator from './src/navigation/RootNavigator';
import { Colors } from './src/theme/colors';

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar
        barStyle="light-content"
        backgroundColor={Colors.background}
        translucent={false}
      />
      <RootNavigator />
    </NavigationContainer>
  );
}